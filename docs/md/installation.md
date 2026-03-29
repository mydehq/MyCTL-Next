# Installation Guide

MyCTL is designed to be easy to install and manage using modern toolchain managers. The primary and recommended way to install MyCTL is via **Mise**.

## Prerequisites

Ensure you have the following installed on your system:
- [**mise**](https://mise.jdx.st/): For toolchain and environment management.
- **Go ≥ 1.26**: For compiling the thin proxy client.
- **Python ≥ 3.13**: For running the intelligent daemon. MyCTL automatically discovers the best available Python on your system `$PATH`, ensuring compatibility with NixOS and non-standard environments.
- **uv**: For lightning-fast Python dependency management.

## 1. Fast Install (Recommended)

The easiest way to get up and running is to use the `mise` build task:

```bash
# Clone the repository
git clone https://github.com/mydehq/MyCTL.git
cd MyCTL

# Install required toolchains automatically
mise install

# Build everything (Go client + Python environment)
mise run build
```

This will:
1.  Compile the Go client into `./bin/myctl`.
2.  Prepare the Python virtual environment and SDK.

## 2. Setting up your PATH

To use `myctl` from anywhere, add the `bin` directory to your shell's configuration (e.g., `.bashrc`, `.zshrc`, or `.bash_profile`):

```bash
export PATH="$HOME/Projects/MyCTL/bin:$PATH"
```

## 3. Persistent Daemon (Optional)

While MyCTL is self-bootstrapping and will start automatically when you run any command, you may prefer to run it as a background service via `systemd`.

Create a user-level service file at `~/.config/systemd/user/myctl.service`:

```ini
[Unit]
Description=MyCTL Intelligent Daemon
After=network.target

[Service]
ExecStart=%h/Projects/MyCTL/daemon/myctl-daemon
Restart=always
Environment=PYTHONPATH=%h/Projects/MyCTL/daemon

[Install]
WantedBy=default.target
```

Then enable and start the service:
```bash
systemctl --user daemon-reload
systemctl --user enable --now myctl
```

---

## 🛠 Troubleshooting

### "Command not found"
Ensure the `bin/` directory is correctly added to your `$PATH` and that you've restarted your terminal or sourced your config.

### Python version mismatch
MyCTL requires Python 3.13+. If your system Python is older, `mise` will automatically install the correct version for you if you run `mise install`.
