# Installation Guide

::: warning 
**{{metadata.title}}** is currently in active development. Features and APIs are subject to change.
:::

To install, ensure you have both <a :href="metadata.miseHome" target="_blank">mise</a> and **uv** installed on your system.

Then, execute these commands to set up the project:

```bash-vue
# Clone the repo
git clone {{metadata.repo}}

# Switch to the next branch (active development)
cd MyCTL
git switch next

# Build the Go proxy
mise run build
```

## The First Run (Cold Boot)

You do **not** need to manually start the daemon. MyCTL is designed to be self-healing. When you run your first command, the Go proxy will detect the missing daemon and trigger a **Cold Boot**:

```bash
myctl ping
```

Depending on your system, the first run may take a few seconds as `uv` creates the isolated virtual environment and syncs dependencies. Subsequent commands will respond in sub-milliseconds.
