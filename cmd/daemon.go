package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"

	"github.com/adrg/xdg"
	"github.com/rs/zerolog/log"
)

func resolveDaemonPaths() (string, string, string, error) {
	if _, err := exec.LookPath("uv"); err != nil {
		return "", "", "", fmt.Errorf("hard dependency 'uv' not found in PATH. Please install uv (https://docs.astral.sh/uv/)")
	}

	_, currentFile, _, _ := runtime.Caller(0)
	daemonRoot := filepath.Join(filepath.Dir(filepath.Dir(currentFile)), "daemon")
	if _, err := filepath.Abs(daemonRoot); err != nil {
		daemonRoot = filepath.Join(xdg.DataHome, "myctl", "daemon")
	}

	venvPath := filepath.Join(xdg.DataHome, "myctl", "venv")
	venvPython := filepath.Join(venvPath, "bin", "python")
	return daemonRoot, venvPath, venvPython, nil
}

func syncDaemonEnvironment(daemonRoot, venvPath string) error {
	syncCmd := exec.Command("uv", "sync", "--project", daemonRoot)
	syncCmd.Env = append(os.Environ(), fmt.Sprintf("UV_PROJECT_ENVIRONMENT=%s", venvPath))
	if output, err := syncCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to sync daemon environment: %v\n%s", err, string(output))
	}
	return nil
}

func buildDaemonCommand(daemonRoot, venvPath, venvPython string) *exec.Cmd {
	cmd := exec.Command(venvPython, "-m", "myctld")
	cmd.Dir = daemonRoot
	cmd.Env = append(os.Environ(),
		fmt.Sprintf("UV_PROJECT_ENVIRONMENT=%s", venvPath),
		fmt.Sprintf("PYTHONPATH=%s", daemonRoot),
	)
	return cmd
}

// RunDaemonForeground runs myctld attached to the current terminal.
func RunDaemonForeground() error {
	daemonRoot, venvPath, venvPython, err := resolveDaemonPaths()
	if err != nil {
		return err
	}

	if err := syncDaemonEnvironment(daemonRoot, venvPath); err != nil {
		return err
	}

	cmd := buildDaemonCommand(daemonRoot, venvPath, venvPython)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin
	return cmd.Run()
}

// BootstrapDaemon launches the Python daemon and waits for the __DAEMON_READY__ signal.
func BootstrapDaemon() error {
	daemonRoot, venvPath, venvPython, err := resolveDaemonPaths()
	if err != nil {
		return err
	}
	if err := syncDaemonEnvironment(daemonRoot, venvPath); err != nil {
		return err
	}

	cmd := buildDaemonCommand(daemonRoot, venvPath, venvPython)

	stdoutPipe, err := cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("could not create stdout pipe for daemon: %v", err)
	}

	log.Info().Msg("Starting Daemon...")
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start daemon process: %v", err)
	}

	scanner := bufio.NewScanner(stdoutPipe)
	for scanner.Scan() {
		line := scanner.Text()
		if line == "__DAEMON_READY__" {
			log.Debug().Msg("Handshake successful: Unblocking proxy.")
			go cmd.Wait()
			return nil
		}
		// Stream the cold boot logs (uv sync, environment setup, etc.)
		fmt.Printf("[myctl-boot] %s\n", line)
	}

	return fmt.Errorf("daemon process terminated prematurely before ready signal")
}
