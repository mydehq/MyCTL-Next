from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import NotRequired, Required, TypedDict, TypeVar


class FlagSpec(TypedDict):
    name: Required[str]
    short: Required[str]
    default: NotRequired[object]
    help: Required[str]
    type: NotRequired[type | None]
    choices: NotRequired[Sequence[object]]
    required: NotRequired[bool]


F = TypeVar("F", bound=Callable[..., object])
CommandFunc = Callable[..., object]


@dataclass(slots=True)
class Plugin:
    name: str | None = None
    _commands: list[CommandFunc] = field(default_factory=list, init=False)
    _load_hooks: list[CommandFunc] = field(default_factory=list, init=False)
    _periodic_hooks: list[tuple[int, CommandFunc]] = field(
        default_factory=list, init=False
    )

    def command(self, path: str, help: str = "") -> Callable[[F], F]:
        """Register a command handler.

        Args:
            path: Command path (e.g., "volume set" for "plugin volume set").
            help: Short help text displayed in schema/CLI.

        Example:
            @plugin.command("volume set", help="Set volume level")
            def set_volume(ctx: Context) -> dict[str, object]:
                return {"status": "ok", "volume": ctx.flags.get("level", 50)}
        """

        def decorator(func: F) -> F:
            setattr(func, "__myctl_cmd__", {"path": path, "help": help})
            self._commands.append(func)
            return func

        return decorator

    def flag(
        self,
        name: str,
        short: str,
        *,
        default: object = None,
        help: str,
        flag_type: type | None = None,
        choices: Sequence[object] | None = None,
        required: bool = False,
    ) -> Callable[[F], F]:
        """Register a single flag on a command handler.

        Args:
            name: Long form (e.g., "level", becomes "--level").
            short: Short form (e.g., "l", becomes "-l").
            default: Default value if flag not provided.
            help: Flag help text.
            flag_type: Expected type (int, str, etc.). Auto-detected from default if not provided.
            choices: Allowed values for this flag.
            required: Whether the flag must be provided.

        Example:
            @plugin.command("greet")
            @plugin.flag("name", "n", default="World", help="Name to greet")
            def greet(ctx: Context) -> str:
                return f"Hello, {ctx.flags['name']}!"
        """

        def decorator(func: F) -> F:
            clean_name = name.lstrip("-").replace("_", "-")
            full_name = "--" + clean_name
            full_short = "-" + short.lstrip("-")
            resolved_type = flag_type or (type(default) if default is not None else str)
            flags = getattr(func, "__myctl_flags__", None)
            if flags is None:
                flags = []
                setattr(func, "__myctl_flags__", flags)
            flags.append(
                {
                    "name": full_name,
                    "short": full_short,
                    "type": resolved_type.__name__
                    if hasattr(resolved_type, "__name__")
                    else "str",
                    "default": default,
                    "required": required,
                    "choices": choices or [],
                    "help": help,
                }
            )
            return func

        return decorator

    def flags(self, items: list[FlagSpec]) -> Callable[[F], F]:
        """Register multiple flags at once using FlagSpec list.

        Args:
            items: List of flag specifications with name, short, default, help, etc.

        Example:
            @plugin.command("setup")
            @plugin.flags([
                {"name": "host", "short": "h", "default": "localhost", "help": "Server host"},
                {"name": "port", "short": "p", "default": 8000, "help": "Server port"},
            ])
            def setup(ctx: Context) -> dict[str, object]:
                return {"host": ctx.flags["host"], "port": ctx.flags["port"]}
        """

        def decorator(func: F) -> F:
            for item in items:
                self.flag(
                    item["name"],
                    item["short"],
                    default=item.get("default"),
                    help=item["help"],
                    flag_type=item.get("type"),
                    choices=item.get("choices"),
                    required=bool(item.get("required", False)),
                )(func)
            return func

        return decorator

    def on_load(self, func: F) -> F:
        """Register a startup hook that runs when the plugin loads.

        The hook receives an optional Context parameter. If the handler accepts
        a Context parameter with type annotation, it will be provided.

        Example:
            @plugin.on_load
            async def setup(ctx: Context) -> None:
                log.info("plugin loaded")
        """
        self._load_hooks.append(func)
        return func

    def periodic(self, seconds: int) -> Callable[[F], F]:
        """Register a background task that runs periodically.

        Args:
            seconds: Interval in seconds between invocations.

        Example:
            @plugin.periodic(60)
            async def update_cache() -> None:
                log.info("cache updated", duration_ms=150)
        """

        def decorator(func: F) -> F:
            self._periodic_hooks.append((seconds, func))
            return func

        return decorator
