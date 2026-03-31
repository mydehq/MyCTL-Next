import asyncio
import json
import logging
import signal
from typing import Callable
from .ipc import Request, err
from .config import SOCKET_PATH, LOG_FILE

# Setup basic logging
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class DaemonServer:
    def __init__(self, registry):
        self.registry = registry
        self.server = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Standard NDJSON IPC Handler"""
        try:
            line = await reader.readline()
            if not line:
                return

            raw_data = json.loads(line.decode().strip())
            req = Request(**raw_data)

            response_data = await self.registry.dispatch(req)

            writer.write(json.dumps(response_data).encode() + b"\n")
            await writer.drain()

        except Exception as e:
            logging.error(f"Internal Engine Error: {str(e)}")
            error_response = err(f"Internal Engine Error: {str(e)}")
            writer.write(json.dumps(error_response).encode() + b"\n")
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        """Launch the Unix Socket Server"""
        # Cleanup stale socket
        if SOCKET_PATH.exists():
            try:
                SOCKET_PATH.unlink()
            except Exception as e:
                logging.error(f"Failed to remove stale socket: {e}")

        # Ensure directory exists
        SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)

        self.server = await asyncio.start_unix_server(
            self.handle_client, path=str(SOCKET_PATH)
        )

        # ── Start Periodic Background Tasks ──────────────
        for interval, func in self.registry.periodic_tasks:
            logging.info(f"Starting background task: {func.__name__} (every {interval}s)")
            asyncio.create_task(self._periodic_wrapper(interval, func))

        # The "Ready Signal" for the Go Proxy
        print("__DAEMON_READY__", flush=True)

        logging.info(f"Daemon listening on {SOCKET_PATH}")

        async with self.server:
            await self.server.serve_forever()

    async def _periodic_wrapper(self, interval: int, func: Callable):
        """Infinite loop for a background task"""
        while True:
            try:
                await asyncio.sleep(interval)
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            except Exception as e:
                logging.error(
                    f"Background task '{func.__name__}' ({interval}s) failed: {e}. "
                    f"Retrying in {interval}s..."
                )

    def stop(self):
        if self.server:
            self.server.close()
