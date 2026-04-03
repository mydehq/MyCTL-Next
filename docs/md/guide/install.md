# Installation Guide

This guide covers the tools you need to install MyCTL and run the first command successfully.

## Prerequisites

Ensure the following tools are available in your system path:

1. **<a :href="metadata.tools.go">Go 1.22+</a>**: Used to build the CLI client.
2. **<a :href="metadata.tools.uv">uv</a>**: Used to manage the Python environment for the daemon.

> [!NOTE]
> You do not need a globally installed Python 3 runtime. `uv` will download and manage a private Python environment for the MyCTL Engine.

---

## Build From Source

MyCTL uses `mise` for task management, but it is optional.

### 1. Build the Client

Compile the client from the project root:

```bash
go build -o ./bin/myctl ./cmd
```

### 2. Verify `uv`

Confirm `uv` is installed:

```bash
uv --version
```

---

## First Run

After building, run a command to start MyCTL and verify the environment:

```bash
./bin/myctl ping
```

Foreground daemon run (attached to current terminal):

```bash
./bin/myctl start
```

Background daemon run (detached):

```bash
./bin/myctl start -b
```

If you want to use the local binary directly, add `./bin` to your shell `PATH`.
