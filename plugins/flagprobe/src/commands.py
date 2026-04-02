from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from myctl.api import Context


def _lookup_flag_value(
    flags: Mapping[str, object], long_name: str
) -> tuple[bool, object]:
    """Resolve a flag value from common key forms used in request payloads."""
    candidates = [
        long_name,
        long_name.replace("-", "_"),
        f"--{long_name}",
    ]
    for key in candidates:
        if key in flags:
            return True, flags[key]
    return False, None


def build_flag_report(ctx: Context, handler: Callable[..., Any]) -> dict[str, object]:
    """Return a diagnostic report of declared flags vs provided values."""
    specs = getattr(handler, "__myctl_flags__", [])

    declared_defaults: dict[str, object] = {}
    resolved: dict[str, object] = {}
    provided_keys: dict[str, object] = dict(ctx.flags)
    missing_flags: list[str] = []

    for spec in specs:
        long_name = str(spec.get("name", "")).lstrip("-")
        default_value = spec.get("default")
        declared_defaults[long_name] = default_value

        found, provided_value = _lookup_flag_value(ctx.flags, long_name)
        if found:
            resolved[long_name] = provided_value
        else:
            resolved[long_name] = default_value
            missing_flags.append(long_name)

    return {
        "plugin": ctx.plugin_id,
        "command": ctx.command_name,
        "provided_flags": provided_keys,
        "declared_defaults": declared_defaults,
        "resolved_values": resolved,
        "missing_from_request": missing_flags,
        "note": "Defaults are declared in metadata; this plugin resolves fallback values explicitly.",
    }
