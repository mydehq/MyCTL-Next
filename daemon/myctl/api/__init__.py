import logging
from myctl.core.ipc import Request, ok, err, Response
from typing import Callable, Any, TypeVar, Optional

F = TypeVar("F", bound=Callable[..., Any])

# ── Internal hooks — injected by the registry during plugin discovery ─────────
_dispatch_hook: Optional[Callable[[Callable], None]] = None
_load_hooks:     list[Callable] = []
_periodic_hooks: list[tuple[int, Callable]] = []

# ── Plugin-scoped Logger ──────────────────────────────────────────────────────
# Points to the generic logger by default; the registry injects a plugin-scoped
# one (myctl.plugin.<id>) during discovery so all plugin log output is namespaced.
logger: logging.Logger = logging.getLogger("myctl.plugin")


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger under the myctl.plugin namespace."""
    return logging.getLogger(f"myctl.plugin.{name}")


class RegistryProxy:
    """
    The public SDK registry interface.
    Delegates all registration calls to the active daemon instance during plugin discovery.
    """

    def add_cmd(self, path: str, help: str = "") -> Callable[[F], F]:
        """Register an async function as a CLI command."""
        def decorator(func: F) -> F:
            func.__myctl_cmd__ = {"path": path, "help": help}
            if _dispatch_hook:
                _dispatch_hook(func)
            return func
        return decorator

    def add_flag(self, name: str, short: str = "", type: type = str, default: Any = None, required: bool = False, choices: list = None, help: str = "") -> Callable[[F], F]:
        """Register a declarative flag for pre-parsing against a CLI command."""
        def decorator(func: F) -> F:
            if not hasattr(func, "__myctl_flags__"):
                func.__myctl_flags__ = []
            func.__myctl_flags__.append({
                "name": name,
                "short": short,
                "type": type.__name__ if hasattr(type, "__name__") else "str",
                "default": default,
                "required": required,
                "choices": choices or [],
                "help": help
            })
            return func
        return decorator

    def on_load(self, func: F) -> F:
        """
        Register an async function to run once after the plugin has been fully loaded.
        Use this for one-time setup (e.g., connecting to DBus, verifying hardware).

        Example:
            @registry.on_load
            async def setup():
                await connect_to_pulseaudio()
        """
        _load_hooks.append(func)
        return func

    def periodic(self, seconds: int) -> Callable[[F], F]:
        """
        Register an async function to run at a specific interval in the background.
        The function starts executing after `on_load` has completed.

        Example:
            @registry.periodic(seconds=60)
            async def update_cache():
                await fetch_remote_data()
        """
        def decorator(func: F) -> F:
            _periodic_hooks.append((seconds, func))
            return func
        return decorator


registry = RegistryProxy()

__all__ = ["Request", "ok", "err", "Response", "registry", "logger", "get_logger"]
