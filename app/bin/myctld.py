#!/usr/bin/env python3
"""
myctld — MyCTL Smart Daemon
Listens on a Unix Domain Socket and dispatches commands to native modules.
"""

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path

# ─── Path Configuration ───────────────────────────────────────────────────

# Ensure 'app' is in sys.path when running from the root or bin dir
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# ─── Constants & Logging ──────────────────────────────────────────────────

XDG_RUNTIME = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
SOCKET_PATH = os.path.join(XDG_RUNTIME, "myctld.sock")
LOG_LEVEL    = os.environ.get("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("myctld")

# ─── Simple Registry ──────────────────────────────────────────────────────

COMMAND_REGISTRY = {}

def register(namespace, cmd_name, help_text=""):
    """Decorator to register a function as a command."""
    def decorator(func):
        if namespace not in COMMAND_REGISTRY:
            COMMAND_REGISTRY[namespace] = {}
        COMMAND_REGISTRY[namespace][cmd_name] = {
            "func": func,
            "help": help_text
        }
        return func
    return decorator

# ─── Initial Core Commands ───────────────────────────────────────────────

@register("core", "ping", help="Test daemon connectivity")
async def ping(request):
    return {"type": "success", "data": "pong", "exit_code": 0}

@register("core", "list", help="List all available namespaces")
async def list_namespaces(request):
    namespaces = sorted(COMMAND_REGISTRY.keys())
    return {"type": "success", "data": "\n".join(namespaces), "exit_code": 0}

# ─── Router ───────────────────────────────────────────────────────────────

async def route(request: dict) -> dict:
    """Dispatch a JSON request to the right registered function."""
    args = request.get("args", [])
    if not args:
        return {"type": "error", "data": "No arguments provided", "exit_code": 1}

    # Format: myctl <namespace> <command> [args...]
    # Case: myctl ping -> mapped to core/ping for convenience
    if len(args) == 1 and args[0] == "ping":
        ns, cmd = "core", "ping"
        sub_args = []
    elif len(args) >= 2:
        ns = args[0]
        cmd = args[1]
        sub_args = args[2:]
    else:
        # Single argument namespaces or unknown
        ns = args[0]
        if ns in COMMAND_REGISTRY:
            # Maybe show help for namespace if only namespace provided
            cmds = ", ".join(COMMAND_REGISTRY[ns].keys())
            return {"type": "success", "data": f"Namespace '{ns}' available commands: {cmds}", "exit_code": 0}
        return {"type": "error", "data": f"Unknown namespace or command: {args}", "exit_code": 1}

    if ns in COMMAND_REGISTRY and cmd in COMMAND_REGISTRY[ns]:
        handler = COMMAND_REGISTRY[ns][cmd]["func"]
        try:
            return await handler(request)
        except Exception as e:
            log.exception("Error in command handler %s/%s", ns, cmd)
            return {"type": "error", "data": str(e), "exit_code": 1}
    
    return {"type": "error", "data": f"Command not found: {ns} {cmd}", "exit_code": 1}

# ─── Connection Handler ───────────────────────────────────────────────────

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        raw = await reader.readline()
        if not raw: return

        request = json.loads(raw)
        log.debug("REQ: %s", request.get("args"))

        response = await route(request)
        log.debug("RES: %s", response.get("type"))

        writer.write((json.dumps(response) + "\n").encode())
        await writer.drain()

    except json.JSONDecodeError:
        err = {"type": "error", "data": "Malformed JSON request", "exit_code": 1}
        writer.write((json.dumps(err) + "\n").encode())
    except Exception as e:
        log.exception("Unhandled IPC error")
        err = {"type": "error", "data": f"Daemon internal error: {e}", "exit_code": 1}
        writer.write((json.dumps(err) + "\n").encode())
    finally:
        writer.close()
        await writer.wait_closed()

# ─── Main ─────────────────────────────────────────────────────────────────

async def main() -> None:
    # ── Singleton check ───────────────────────────────────────────
    if os.path.exists(SOCKET_PATH):
        try:
            _, _ = await asyncio.open_unix_connection(SOCKET_PATH)
            print(f"error: myctld is already running (socket active at {SOCKET_PATH})", file=sys.stderr)
            sys.exit(1)
        except (ConnectionRefusedError, OSError):
            os.unlink(SOCKET_PATH)
            log.debug("Removed stale socket at %s", SOCKET_PATH)

    try:
        server = await asyncio.start_unix_server(handle_client, path=SOCKET_PATH)
    except Exception as e:
        print(f"error: could not start server: {e}", file=sys.stderr)
        sys.exit(1)

    log.info("myctld listening on %s (Rebooted)", SOCKET_PATH)

    loop = asyncio.get_running_loop()
    def _shutdown():
        log.info("Shutting down...")
        server.close()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            pass

    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)
    log.info("myctld stopped.")

if __name__ == "__main__":
    asyncio.run(main())
