import logging
from contextvars import ContextVar, Token

_CURRENT_PLUGIN_ID: ContextVar[str] = ContextVar(
    "myctl_current_plugin_id", default="core"
)


class _LoggerProxy:
    """Context-aware logger proxy for plugin authors.

    Uses the current plugin context (bound by the registry at dispatch time)
    so calls like `log.info(...)` route to `myctl.plugin.<plugin_id>`.
    """

    def _logger(self) -> logging.Logger:
        plugin_id = _CURRENT_PLUGIN_ID.get() or "core"
        return logging.getLogger(f"myctl.plugin.{plugin_id}")

    def debug(self, msg, *args, **kwargs):
        self._logger().debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._logger().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._logger().exception(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._logger().critical(msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        self._logger().log(level, msg, *args, **kwargs)


# Public API: supports `from myctl.api import log` then `log.info(...)`
log = _LoggerProxy()


def bind_logger_plugin(plugin_id: str) -> Token:
    """Bind logger context to a plugin id and return reset token."""
    return _CURRENT_PLUGIN_ID.set(plugin_id)


def reset_logger_plugin(token: Token):
    """Restore previous logger context."""
    _CURRENT_PLUGIN_ID.reset(token)
