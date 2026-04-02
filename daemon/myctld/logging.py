"""Logging setup for file JSONL logs and optional console logs.

The daemon writes durable structured logs (JSONL) for tooling and debugging,
and can also emit compact human-readable console logs for foreground runs.
Keeping both concerns in one module ensures consistent formatting and handler
configuration across startup paths.

``from __future__ import annotations`` is used to postpone hint evaluation and
keep imports predictable in typed modules.

Read before: daemon/myctld/ipc.py; read after: daemon/myctld/registry.py
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from myctl.api.logger import _ContextFilter


@dataclass(slots=True)
class LogRecordData:
    ts: str
    level: str
    component: str
    message: str
    request_id: str | None = None
    plugin_id: str | None = None
    command_name: str | None = None
    hook_name: str | None = None
    event: str | None = None
    error_code: str | None = None
    duration_ms: int | None = None
    fields: dict[str, object] | None = None


class JsonlFormatter(logging.Formatter):
    """Emit structured JSON log lines for durable daemon log files."""

    def format(self, record: logging.LogRecord) -> str:
        fields_value = getattr(record, "fields", None)
        # Enforce object shape for extra fields so downstream log processors
        # receive predictable JSON structures.
        fields = fields_value if isinstance(fields_value, dict) else {}
        payload = LogRecordData(
            ts=datetime.now(timezone.utc).isoformat(),
            level=record.levelname,
            component=getattr(record, "component", record.name),
            message=record.getMessage(),
            request_id=getattr(record, "request_id", None),
            plugin_id=getattr(record, "plugin_id", None),
            command_name=getattr(record, "command_name", None),
            hook_name=getattr(record, "hook_name", None),
            event=getattr(record, "event", None),
            error_code=getattr(record, "error_code", None),
            duration_ms=getattr(record, "duration_ms", None),
            fields=fields,
        )
        return json.dumps(asdict(payload), ensure_ascii=True)


class ConsoleFormatter(logging.Formatter):
    """Emit compact human-readable console log lines."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        return f"[{ts}] [{record.levelname}] {record.getMessage()}"


def configure_logging(log_file: Path, level: int = logging.INFO) -> None:
    """Configure root logger handlers for daemon runtime."""
    # Ensure destination exists before handlers are created.
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)

    # File formatter can be configured via MYCTLD_FILE_LOG_FORMAT=[json|human].
    # Default behavior is human-readable for easier local debugging.
    file_format = os.getenv("MYCTLD_FILE_LOG_FORMAT", "human").strip().lower()
    if file_format in {"human", "text", "console"}:
        file_handler.setFormatter(ConsoleFormatter())
    else:
        file_handler.setFormatter(JsonlFormatter())

    # Console logging defaults to enabled for direct runs and can be disabled
    # explicitly (used by the client bootstrap path).
    console_flag = os.getenv("MYCTLD_CONSOLE_LOG", "1").strip().lower()
    console_enabled = console_flag not in {"0", "false", "no", "off"}

    root = logging.getLogger()
    # Replace previous handlers to avoid duplicate lines when tests or
    # restarts configure logging more than once in one process.
    root.handlers.clear()
    root.filters.clear()
    root.addFilter(_ContextFilter())
    root.setLevel(level)
    root.addHandler(file_handler)
    if console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ConsoleFormatter())
        root.addHandler(console_handler)
