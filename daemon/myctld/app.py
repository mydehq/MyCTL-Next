"""Async daemon server lifecycle and IPC request loop.

This module is the runtime entry for myctld. It wires together:
- socket startup and single-instance guard
- request parsing/context construction
- command dispatch through the registry
- graceful shutdown on stop/signal

The module imports ``annotations`` from ``__future__`` so type hints can refer
to symbols that are defined later without forcing immediate runtime evaluation.

Read before: daemon/myctld/config.py; read after: daemon/myctld/registry.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import socket

from pydantic import ValidationError

from myctl.api.context import Response, ResponseStatus
from myctl.api.logger import bind_logger_context, reset_logger_context

from .config import APP_NAME, LOG_FILE, PLUGIN_SEARCH_PATHS, SOCKET_PATH
from .ipc import encode_response, make_context, parse_request
from .logging import configure_logging
from .registry import Registry
from .plugin.manager import PluginManager


logger = logging.getLogger(APP_NAME)


class DaemonServer:
    """Owns the Unix socket server and request handling lifecycle."""

    def __init__(self, registry: Registry):
        self.registry = registry
        self.server: asyncio.AbstractServer | None = None
        self._shutdown_event = asyncio.Event()

    def request_shutdown(self, reason: str | None = None) -> None:
        """Signal daemon shutdown and optionally print a human-facing reason."""
        if self._shutdown_event.is_set():
            return
        if reason:
            print(reason, flush=True)
        self._shutdown_event.set()

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Handle one NDJSON client session from request to final response.

        The protocol supports both single-shot responses and interactive
        ask/reply flows over the same socket.
        """
        try:
            # Phase 1: read exactly one request line from this connection.
            line = await reader.readline()
            if not line:
                return

            # Phase 2: parse and minimally validate raw payload.
            raw_data = parse_request(line)
            if "terminal" not in raw_data:
                # Terminal metadata is required so plugins can adapt behavior
                # (TTY-aware prompts/colors/stream handling) to client context.
                writer.write(
                    encode_response(
                        Response(
                            status=ResponseStatus.ERROR,
                            data="Invalid request: missing required 'terminal' metadata",
                            exit_code=1,
                        )
                    )
                )
                await writer.drain()
                return

            try:
                # Phase 3: build strongly-typed context object used everywhere
                # below (system commands, plugins, logging hooks).
                ctx = make_context(raw_data)
            except ValidationError as exc:
                writer.write(
                    encode_response(
                        Response(
                            status=ResponseStatus.ERROR,
                            data=f"Invalid request payload: {exc}",
                            exit_code=1,
                        )
                    )
                )
                await writer.drain()
                return

            request_token = bind_logger_context(
                request_id=ctx.request_id,
                command_name=ctx.command_name,
                plugin_id="core",
            )

            async def ask_cb(prompt: str, secret: bool = False) -> str:
                """Bridge plugin `ctx.ask(...)` to client prompt-response IPC."""
                # status=2 is an out-of-band interactive prompt message.
                # The client should display prompt and return one answer line.
                writer.write(
                    json.dumps(
                        {
                            "status": 2,
                            "data": {"prompt": prompt, "secret": bool(secret)},
                            "exit_code": 0,
                        }
                    ).encode()
                    + b"\n"
                )
                await writer.drain()
                answer_line = await reader.readline()
                if not answer_line:
                    raise EOFError("Client disconnected during prompt")
                try:
                    answer_data = json.loads(answer_line.decode().strip())
                    return str(answer_data.get("data", ""))
                except json.JSONDecodeError:
                    return answer_line.decode().strip()

            ctx.bind_ask_callback(ask_cb)

            # Phase 4: dispatch once and send exactly one final response.
            try:
                response = await self.registry.dispatch(ctx)
                writer.write(encode_response(response))
                await writer.drain()
                if (
                    response.status == ResponseStatus.OK
                    and isinstance(ctx.path, list)
                    and len(ctx.path) > 0
                    and ctx.path[0] in {"stop", "restart"}
                ):
                    # Defer shutdown until after stop/restart response is flushed
                    # so the requesting client gets a deterministic success reply.
                    self.request_shutdown()
            finally:
                reset_logger_context(request_token)
        except Exception as exc:
            # Last-resort conversion of unexpected exceptions into protocol
            # errors so clients never hang without a response.
            writer.write(
                encode_response(
                    Response(
                        status=ResponseStatus.ERROR,
                        data=f"Internal Engine Error: {exc}",
                        exit_code=1,
                    )
                )
            )
            await writer.drain()
        finally:
            # Always close per-connection resources, regardless of success/fail.
            writer.close()
            await writer.wait_closed()

    async def start(self) -> None:
        """Start the socket server, wait for shutdown signal, and clean up."""
        if SOCKET_PATH.exists():
            # Guard against duplicate daemon instances. Only remove stale sockets.
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                if probe.connect_ex(str(SOCKET_PATH)) == 0:
                    raise RuntimeError(
                        f"daemon already running (socket: {SOCKET_PATH})"
                    )
            try:
                SOCKET_PATH.unlink()
            except OSError as exc:
                raise RuntimeError(
                    f"failed to remove stale socket {SOCKET_PATH}: {exc}"
                ) from exc
        SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Bind Unix socket and attach session handler.
        self.server = await asyncio.start_unix_server(
            self.handle_client, path=str(SOCKET_PATH)
        )

        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: self.request_shutdown(
                        f"Received {s.name}. Shutting down {APP_NAME}..."
                    ),
                )
            except NotImplementedError:
                # add_signal_handler is not available on all platforms.
                pass

        print("__DAEMON_READY__", flush=True)
        # Everything below this line is operational visibility for operators.
        logger.info("%s ready", APP_NAME)
        logger.info("listening on %s", SOCKET_PATH)
        logger.info("loaded plugins: %d", len(self.registry.plugins))
        try:
            async with self.server:
                # Keep serving until a stop command or signal triggers shutdown.
                await self._shutdown_event.wait()
        finally:
            logger.info("shutting down %s", APP_NAME)
            self.server.close()
            await self.server.wait_closed()
            try:
                if SOCKET_PATH.exists():
                    # Best-effort cleanup to avoid stale socket blocking restart.
                    SOCKET_PATH.unlink()
            except OSError:
                pass


async def main() -> int:
    """Initialize daemon subsystems and run until shutdown."""
    # Boot order matters: logging first so all startup steps are observable.
    configure_logging(LOG_FILE)
    logger.info("starting %s", APP_NAME)
    # Discover plugins before serving so schema/status are immediately correct.
    plugin_manager = PluginManager(PLUGIN_SEARCH_PATHS)
    discovered = plugin_manager.discover()
    registry = Registry(plugins=discovered)

    # Enforce reserved system command IDs are not used by plugins.
    reserved_names = set(registry.system_help().keys())
    conflicting = sorted(set(discovered.keys()) & reserved_names)
    if conflicting:
        raise RuntimeError(
            f"Plugin IDs conflict with reserved system commands: {', '.join(conflicting)}"
        )

    server = DaemonServer(registry)
    try:
        await server.start()
    except KeyboardInterrupt:
        server.request_shutdown()
    return 0
