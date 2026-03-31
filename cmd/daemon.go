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

// BootstrapDaemon launches the Python daemon and waits for the __DAEMON_READY__ signal.
func BootstrapDaemon() error {
	// 0. Ensure 'uv' is installed
	if _, err := exec.LookPath("uv"); err != nil {
		return fmt.Errorf("hard dependency 'uv' not found in PATH. Please install uv (https://docs.astral.sh/uv/)")
	}

	_, currentFile, _, _ := runtime.Caller(0)

	// In the build phase, find relative paths
	daemonRoot := filepath.Join(filepath.Dir(filepath.Dir(currentFile)), "daemon")
	daemonScript := filepath.Join(daemonRoot, "myctld")

	// Fallback to absolute system path if bin path is relative/missing (Production)
	if _, err := filepath.Abs(daemonScript); err != nil {
		daemonRoot = filepath.Join(xdg.DataHome, "myctl", "daemon")
		daemonScript = filepath.Join(daemonRoot, "myctld")
	}

	// venv location: $XDG_DATA_HOME/myctl/venv
	venvPath := filepath.Join(xdg.DataHome, "myctl", "venv")

	// Execute via 'uv run' to ensure managed python and synced environment
	cmd := exec.Command("uv", "run", "--project", daemonRoot, "python", daemonScript)
	cmd.Env = append(os.Environ(), fmt.Sprintf("UV_PROJECT_ENVIRONMENT=%s", venvPath))

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
