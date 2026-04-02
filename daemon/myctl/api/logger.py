from __future__ import annotations

import logging
from contextvars import ContextVar, Token
from typing import Any

_CURRENT_LOG_CONTEXT: ContextVar[dict[str, object]] = ContextVar(
    "myctl_current_log_context", default={}
)


def _current_context() -> dict[str, object]:
    return dict(_CURRENT_LOG_CONTEXT.get())


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        context = _CURRENT_LOG_CONTEXT.get()

        if not hasattr(record, "component"):
            record.component = record.name

        for key in (
            "request_id",
            "plugin_id",
            "command_name",
            "hook_name",
            "event",
            "error_code",
            "duration_ms",
        ):
            if key in context and not hasattr(record, key):
                setattr(record, key, context[key])

        context_fields = context.get("fields", {})
        record_fields = getattr(record, "fields", {})
        merged_fields: dict[str, object] = {}
        if isinstance(context_fields, dict):
            merged_fields.update(context_fields)
        if isinstance(record_fields, dict):
            merged_fields.update(record_fields)
        record.fields = merged_fields
        return True


def bind_logger_context(**fields: object) -> Token[dict[str, object]]:
    current = _current_context()
    for key, value in fields.items():
        if value is not None:
            current[key] = value
    return _CURRENT_LOG_CONTEXT.set(current)


def reset_logger_context(token: Token[dict[str, object]]) -> None:
    _CURRENT_LOG_CONTEXT.reset(token)


class _LoggerProxy:
    def _logger(self) -> logging.Logger:
        plugin_id = str(_CURRENT_LOG_CONTEXT.get().get("plugin_id") or "core")
        return logging.getLogger(f"myctl.plugin.{plugin_id}")

    def _emit(
        self,
        level: int,
        msg: str,
        *args: Any,
        exc_info: bool
        | BaseException
        | tuple[type[BaseException], BaseException, object]
        | None = None,
        stack_info: bool = False,
        stacklevel: int = 2,
        **fields: Any,
    ) -> None:
        self._logger().log(
            level,
            msg,
            *args,
            extra={"fields": fields},
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel,
        )

    def debug(self, msg: str, *args: Any, **fields: Any) -> None:
        self._emit(logging.DEBUG, msg, *args, **fields)

    def info(self, msg: str, *args: Any, **fields: Any) -> None:
        self._emit(logging.INFO, msg, *args, **fields)

    def warning(self, msg: str, *args: Any, **fields: Any) -> None:
        self._emit(logging.WARNING, msg, *args, **fields)

    def error(self, msg: str, *args: Any, **fields: Any) -> None:
        self._emit(logging.ERROR, msg, *args, **fields)

    def exception(self, msg: str, *args: Any, **fields: Any) -> None:
        self._emit(logging.ERROR, msg, *args, exc_info=True, **fields)

    def critical(self, msg: str, *args: Any, **fields: Any) -> None:
        self._emit(logging.CRITICAL, msg, *args, **fields)

    def log(self, level: int, msg: str, *args: Any, **fields: Any) -> None:
        self._emit(level, msg, *args, **fields)


log = _LoggerProxy()


def bind_logger_plugin(plugin_id: str) -> Token[str]:
    return bind_logger_context(plugin_id=plugin_id)


def reset_logger_plugin(token: Token[str]) -> None:
    reset_logger_context(token)
