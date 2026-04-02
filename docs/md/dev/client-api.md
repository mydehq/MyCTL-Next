# Client API (IPC)

This page is for **client implementers** building custom frontends, wrappers, TUI clients, or automation tooling that talks directly to the MyCTL daemon.

For full wire details, see [IPC Protocol](../technical/core-runtime/ipc-protocol.md).

## Endpoint & Transport

- Transport: Unix domain socket
- Framing: NDJSON (one JSON object per line)
- Socket path: `$XDG_RUNTIME_DIR/myctl/myctld.sock`

Each request is one JSON line terminated by `\n`. Each response is one JSON line terminated by `\n`.

## Request Contract

```json
{
  "path": ["audio", "status"],
  "args": [],
  "cwd": "/home/user/project",
  "terminal": {
    "is_tty": true,
    "color_depth": "16",
    "no_color": false
  },
  "env": {
    "USER": "soymadip"
  }
}
```

### Required fields

- `path`: command segments (`["schema"]`, `["audio", "status"]`, etc.)
- `terminal`: rendering capability block (`is_tty`, `color_depth`, `no_color`)

### Optional fields

- `args`: argument list intended for the final handler
- `cwd`: caller working directory
- `env`: caller environment projection

> [!IMPORTANT]
> `terminal` is required. Omit it and the daemon returns an error response.

## Response Contract

```json
{
  "status": 0,
  "data": "pong",
  "exit_code": 0
}
```

Status codes:

- `0`: `OK`
- `1`: `ERROR`
- `2`: `ASK` (interactive prompt flow)

## Interactive Flow (`status == 2`)

If daemon returns `status: 2`, `data` contains a prompt object:

```json
{
  "status": 2,
  "data": { "prompt": "Password: ", "secret": true },
  "exit_code": 0
}
```

Client must respond on the **same open socket** with:

```json
{ "data": "user input" }
```

Continue reading until final status is `0` or `1`.

## Core Commands for Clients

### Discovery

- `schema`: returns full command tree for dynamic client command generation.

### Health & lifecycle

- `ping`
- `status`
- `start`
- `restart`
- `stop`
- `logs`
- `help`
- `sdk`

## Typical Client Startup Sequence

1. Connect to socket.
2. If connect fails, run client bootstrap policy (or surface daemon-offline).
3. Call `schema` and cache command tree.
4. Render/route user command.
5. Send execution request and print output based on `status/data/exit_code`.

## Error-Handling Guidelines

- Treat socket connect failures as transport errors.
- Treat `status: 1` as command-level failures and present `data` to users.
- Preserve daemon `exit_code` for shell automation compatibility.
- For direct machine consumption, avoid stripping ANSI unless requested.

## Example: Raw Probe

```bash
echo '{"path":["ping"],"args":[],"cwd":"/tmp","terminal":{"is_tty":true,"color_depth":"16","no_color":false},"env":{"USER":"me"}}' | nc -U "$XDG_RUNTIME_DIR/myctl/myctld.sock"
```

## Compatibility Notes

- Build clients against the current `schema` command contract, not legacy `__sys_*` names.
- Reserve unknown top-level command paths for plugins discovered at runtime.
- Do not assume static command trees across daemon restarts.
