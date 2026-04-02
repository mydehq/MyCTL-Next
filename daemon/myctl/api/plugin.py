from typing import Callable, Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

class Plugin:
    """
    MyCTL Plugin Router.
    """
    def __init__(self, name: str):
        self.name = name
        self._commands = []
        self._load_hooks = []
        self._periodic_hooks = []
        
    def command(self, path: str, help: str = "") -> Callable[[F], F]:
        """Register an async function as a CLI command."""
        def decorator(func: F) -> F:
            func.__myctl_cmd__ = {"path": path, "help": help}
            self._commands.append(func)
            return func
        return decorator

    def flag(
        self,
        name: str,
        short: str,
        default: Any = None,
        help: str = "",
        *,
        flag_type: type = None,
        choices: list = None,
        required: bool = False,
    ) -> Callable[[F], F]:
        """
        Register a declarative flag for pre-parsing against a CLI command.
        """
        def decorator(func: F) -> F:
            clean_name = name.lstrip("-").replace("_", "-")
            full_name = "--" + clean_name
            full_short = "-" + short.lstrip("-")
            
            f_type = flag_type
            if f_type is None:
                f_type = type(default) if default is not None else str

            if not hasattr(func, "__myctl_flags__"):
                func.__myctl_flags__ = []
            func.__myctl_flags__.append(
                {
                    "name": full_name,
                    "short": full_short,
                    "type": f_type.__name__ if hasattr(f_type, "__name__") else "str",
                    "default": default,
                    "required": required,
                    "choices": choices or [],
                    "help": help,
                }
            )
            return func
        return decorator

    def on_load(self, func: F) -> F:
        """Register a hook to run on plugin load."""
        self._load_hooks.append(func)
        return func

    def periodic(self, seconds: int) -> Callable[[F], F]:
        """Register a background task."""
        def decorator(func: F) -> F:
            self._periodic_hooks.append((seconds, func))
            return func
        return decorator
