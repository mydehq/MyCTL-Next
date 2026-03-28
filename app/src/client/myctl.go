package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"time"
)

type Request struct {
	Args []string          `json:"args"`
	Cwd  string            `json:"cwd"`
	Env  map[string]string `json:"env"`
}

type Response struct {
	Type     string `json:"type"`
	Data     string `json:"data,omitempty"`
	ExitCode int    `json:"exit_code"`
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <namespace> <command> [args...]\n", filepath.Base(os.Args[0]))
		os.Exit(1)
	}

	runtimeDir := os.Getenv("XDG_RUNTIME_DIR")
	if runtimeDir == "" {
		runtimeDir = fmt.Sprintf("/run/user/%d", os.Getuid())
	}
	sockPath := filepath.Join(runtimeDir, "myctld.sock")

	// 1. Connect to UDS (No auto-start as per plan)
	conn, err := net.DialTimeout("unix", sockPath, 2*time.Second)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: myctld is not running (socket missing: %s)\n", sockPath)
		os.Exit(1)
	}
	defer conn.Close()

	// 2. Prepare request (Dumb transport)
	cwd, _ := os.Getwd()
	req := Request{
		Args: os.Args[1:],
		Cwd:  cwd,
		Env:  make(map[string]string),
	}
	
	// Minimal env passing (optional, but good for context)
	req.Env["LANG"] = os.Getenv("LANG")
	req.Env["TERM"] = os.Getenv("TERM")

	reqData, err := json.Marshal(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: serialization failure: %v\n", err)
		os.Exit(1)
	}

	// 3. Send request + newline
	_, err = conn.Write(append(reqData, '\n'))
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: write failure: %v\n", err)
		os.Exit(1)
	}

	// 4. Read response
	decoder := json.NewDecoder(conn)
	var resp Response
	err = decoder.Decode(&resp)
	if err != nil && err != io.EOF {
		fmt.Fprintf(os.Stderr, "error: protocol failure: %v\n", err)
		os.Exit(1)
	}

	// 5. Render to user
	if resp.Type == "error" {
		fmt.Fprintf(os.Stderr, "error: %s\n", resp.Data)
	} else {
		if resp.Data != "" {
			fmt.Println(resp.Data)
		}
	}

	os.Exit(resp.ExitCode)
}
