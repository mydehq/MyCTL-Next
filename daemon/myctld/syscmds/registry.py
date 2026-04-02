"""Registration helpers for daemon built-in commands."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from myctl.api.plugin import FlagSpec

SystemCommandHandler = Callable[..., object]

SYSTEM_COMMAND_HANDLERS: dict[str, SystemCommandHandler] = {}
SYSTEM_COMMAND_HELP: dict[str, str] = {}


def _normalize_flag_spec(
    name: str,
    short: str,
    default: object = None,
    help: str = "",
    *,
    flag_type: type | None = None,
    choices: Sequence[object] | None = None,
    required: bool = False,
) -> FlagSpec:
    clean_name = name.lstrip("-").replace("_", "-")
    full_name = "--" + clean_name
    full_short = "-" + short.lstrip("-")
    resolved_type = flag_type or (type(default) if default is not None else str)
    return {
        "name": full_name,
        "short": full_short,
        "type": resolved_type.__name__ if hasattr(resolved_type, "__name__") else "str",
        "default": default,
        "required": required,
        "choices": choices or [],
        "help": help,
    }


def flag(
    name: str,
    short: str,
    default: object = None,
    help: str = "",
    *,
    flag_type: type | None = None,
    choices: Sequence[object] | None = None,
    required: bool = False,
) -> Callable[[SystemCommandHandler], SystemCommandHandler]:
    """Attach a flag metadata entry to a built-in command handler."""

    def decorator(func: SystemCommandHandler) -> SystemCommandHandler:
        flags = getattr(func, "__myctl_flags__", None)
        if flags is None:
            flags = []
            setattr(func, "__myctl_flags__", flags)

        flags.append(
            _normalize_flag_spec(
                name,
                short,
                default,
                help,
                flag_type=flag_type,
                choices=choices,
                required=required,
            )
        )
        return func

    return decorator


def flags(
    items: list[FlagSpec],
) -> Callable[[SystemCommandHandler], SystemCommandHandler]:
    """Attach multiple flag metadata entries to a built-in command handler."""

    def decorator(func: SystemCommandHandler) -> SystemCommandHandler:
        for item in items:
            flag(
                item["name"],
                item["short"],
                item.get("default"),
                item.get("help", ""),
                flag_type=item.get("type"),
                choices=item.get("choices"),
                required=bool(item.get("required", False)),
            )(func)
        return func

    return decorator


def command(
    name: str,
    help: str = "",
    *,
    flags: list[FlagSpec] | None = None,
) -> Callable[[SystemCommandHandler], SystemCommandHandler]:
    """Register a built-in command handler and its help text."""

    def decorator(func: SystemCommandHandler) -> SystemCommandHandler:
        SYSTEM_COMMAND_HANDLERS[name] = func
        SYSTEM_COMMAND_HELP[name] = help
        # Mirror plugin-style metadata so schema generation can treat
        # space-delimited paths as nested command groups.
        setattr(func, "__myctl_cmd__", {"path": name, "help": help})

        if flags:
            for item in flags:
                flag(
                    item["name"],
                    item["short"],
                    item.get("default"),
                    item.get("help", ""),
                    flag_type=item.get("type"),
                    choices=item.get("choices"),
                    required=bool(item.get("required", False)),
                )(func)

        return func

    return decorator
