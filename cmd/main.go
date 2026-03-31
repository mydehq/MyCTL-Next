/*
MyCTL Lean Client Proxy (V2.5 - UV-Native)
Sub-millisecond CLI router that dynamically retrieves its command tree 
from a persistent Python daemon.
*/
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/adrg/xdg"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
)

// ── Types ───────────────────────────────────────────────────────────────────

type Request struct {
	Path []string          `json:"path"`
	Args []string          `json:"args"`
	Cwd  string            `json:"cwd"`
	Env  map[string]string `json:"env"`
}

type Response struct {
	Status   string      `json:"status"`
	Data     interface{} `json:"data"`
	ExitCode int         `json:"exit_code"`
}

type CommandNode struct {
	Type     string                 `json:"type"`
	Help     string                 `json:"help"`
	Children map[string]CommandNode `json:"children,omitempty"`
}

// ── Globals & Init ──────────────────────────────────────────────────────────

var background bool

func init() {
	cw := zerolog.ConsoleWriter{
		Out:        os.Stderr,
		TimeFormat: "15:04:05",
		FormatLevel: func(i interface{}) string {
			if i == nil { return "" }
			level := strings.ToUpper(fmt.Sprintf("%s", i))
			switch level {
			case "INFO": return "\x1b[36m" + level + "\x1b[0m"
			case "ERROR", "FATAL": return "\x1b[31m" + level + "\x1b[0m"
			case "DEBUG", "WARN": return "\x1b[33m" + level + "\x1b[0m"
			default: return level
			}
		},
		FormatFieldName:  func(i interface{}) string { return "" },
		FormatFieldValue: func(i interface{}) string { return fmt.Sprintf(": %s", i) },
	}
	log.Logger = log.Output(cw)

	if os.Getenv("DEBUG") != "" {
		zerolog.SetGlobalLevel(zerolog.DebugLevel)
	} else {
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
	}
}

// ── IPC Layer ───────────────────────────────────────────────────────────────

func getSocketPath() string {
	return filepath.Join(xdg.RuntimeDir, "myctl", "myctld.sock")
}

func getLogPath() string {
	return filepath.Join(xdg.StateHome, "myctl", "daemon.log")
}

func sendIPCRequest(req Request, allowBootstrap bool) (*Response, error) {
	if req.Args == nil {
		req.Args = []string{}
	}
	if req.Env == nil {
		req.Env = make(map[string]string)
	}

	reqBytes, _ := json.Marshal(req)
	reqBytes = append(reqBytes, '\n')

	sockPath := getSocketPath()
	conn, err := net.Dial("unix", sockPath)
	if err != nil {
		if !allowBootstrap {
			return nil, fmt.Errorf("daemon is offline")
		}

		log.Debug().Msg("Daemon socket not found. Attempting cold boot...")
		if err := BootstrapDaemon(); err != nil {
			return nil, fmt.Errorf("daemon cold-boot failed: %v", err)
		}

		conn, err = net.Dial("unix", sockPath)
		if err != nil {
			return nil, fmt.Errorf("daemon unreachable after handshake: %v", err)
		}
	}
	defer conn.Close()

	if _, err = conn.Write(reqBytes); err != nil {
		return nil, err
	}

	respLine, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return nil, err
	}

	var resp Response
	if err = json.Unmarshal([]byte(respLine), &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// ── Schema Layer ─────────────────────────────────────────────────────────────

func fetchSchema(allowBootstrap bool) (map[string]CommandNode, error) {
	req := Request{Path: []string{"__sys_schema"}}
	resp, err := sendIPCRequest(req, allowBootstrap)
	if err != nil {
		return nil, err
	}

	if resp.Status != "ok" {
		return nil, fmt.Errorf("schema error: %v", resp.Data)
	}

	b, _ := json.Marshal(resp.Data)
	var schema map[string]CommandNode
	_ = json.Unmarshal(b, &schema)
	return schema, nil
}

// ── Command Dispatcher ───────────────────────────────────────────────────────

func tailLogs() {
	logPath := getLogPath()
	for i := 0; i < 20; i++ {
		if _, err := os.Stat(logPath); err == nil { break }
		time.Sleep(500 * time.Millisecond) // retry
	}

	cmd := exec.Command("tail", "-f", "-n", "30", logPath)
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	_ = cmd.Run()
}

func executeDaemonCommand(path []string, _ []string) {
	cwd, _ := os.Getwd()
	req := Request{
		Path: path,
		Args: os.Args[1:], // Pass all raw args to Python
		Cwd:  cwd,
		Env:  make(map[string]string),
	}

	resp, err := sendIPCRequest(req, true)
	if err != nil {
		log.Fatal().Err(err).Msg("IPC communication failed")
	}

	if resp.Status != "ok" {
		fmt.Fprintf(os.Stderr, "\x1b[31mError:\x1b[0m %v\n", resp.Data)
	} else {
		switch v := resp.Data.(type) {
		case string:
			if v != "" { fmt.Fprintln(os.Stdout, v) }
		default:
			pretty, _ := json.MarshalIndent(v, "", "  ")
			fmt.Fprintln(os.Stdout, string(pretty))
		}
	}

	// Foreground log handling for start/logs
	if len(path) > 0 {
		name := path[len(path)-1]
		if (name == "start" || name == "logs") && !background {
			log.Info().Msg("Following logs (CTRL-C to detach)...")
			tailLogs()
		}
	}

	os.Exit(resp.ExitCode)
}

// ── Cobra Bridge ─────────────────────────────────────────────────────────────

func buildCobraCommand(name string, node CommandNode, parentPath []string) *cobra.Command {
	currentPath := append(append([]string{}, parentPath...), name)
	cmd := &cobra.Command{
		Use:   name,
		Short: node.Help,
		Run: func(cmd *cobra.Command, args []string) {
			if node.Type == "group" && len(args) == 0 {
				cmd.Help()
				return
			}
			executeDaemonCommand(currentPath, args)
		},
	}
	cmd.FParseErrWhitelist.UnknownFlags = true

	for childName, childNode := range node.Children {
		cmd.AddCommand(buildCobraCommand(childName, childNode, currentPath))
	}
	return cmd
}

// ── Main ─────────────────────────────────────────────────────────────────────

func main() {
	// 1. Intercept 'stop' and 'status' (avoid cold-boot if dead)
	if len(os.Args) > 1 {
		arg := os.Args[1]
		isStop := arg == "stop" || (arg == "daemon" && len(os.Args) > 2 && os.Args[2] == "stop")
		isStatus := arg == "status" || (arg == "daemon" && len(os.Args) > 2 && os.Args[2] == "status")

		if isStop || isStatus {
			_, err := fetchSchema(false)
			if err != nil {
				if isStatus {
					fmt.Println("Daemon Status: offline")
				} else {
					fmt.Println("Daemon is already offline.")
				}
				os.Exit(0)
			}
		}
	}

	// 2. Fetch Dynamic Schema
	schema, err := fetchSchema(true)
	if err != nil {
		log.Warn().Err(err).Msg("Schema fetch failed. Proxying directly.")
		executeDaemonCommand(os.Args[1:], os.Args[1:])
		return
	}

	// 3. Build & Execute Cobra Tree
	rootCmd := &cobra.Command{
		Use:   "myctl",
		Short: "MyCTL: High-Performance Desktop Controller",
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) == 0 {
				cmd.Help()
				return
			}
			executeDaemonCommand(args, args)
		},
	}
	rootCmd.FParseErrWhitelist.UnknownFlags = true
	rootCmd.PersistentFlags().BoolVarP(&background, "background", "b", false, "Run in background")

	for name, node := range schema {
		rootCmd.AddCommand(buildCobraCommand(name, node, []string{}))
	}

	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}
