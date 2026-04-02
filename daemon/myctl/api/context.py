from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal
from uuid import uuid4


class ResponseStatus(IntEnum):
    OK = 0
    ERROR = 1
    ASK = 2


@dataclass(slots=True)
class TerminalContext:
    is_tty: bool = False
    color_depth: Literal["none", "16", "256", "truecolor"] = "none"
    no_color: bool = True


@dataclass(slots=True)
class UserContext:
    name: str = "unknown"
    id: int | None = None


@dataclass(slots=True)
class Response:
    status: ResponseStatus = ResponseStatus.OK
    data: object = ""
    exit_code: int = 0


@dataclass(slots=True)
class Context:
    path: list[str] = field(default_factory=list)
    args: list[str] = field(default_factory=list)
    flags: dict[str, object] = field(default_factory=dict)
    cwd: str = "."
    env: dict[str, str] = field(default_factory=dict)
    user: UserContext = field(default_factory=UserContext)
    terminal: TerminalContext = field(default_factory=TerminalContext)
    request_id: str = field(default_factory=lambda: uuid4().hex)
    command_name: str = ""
    plugin_id: str = ""
    _ask_callback: Callable[[str, bool], Awaitable[str]] | None = field(
        default=None, repr=False, compare=False
    )

    async def ask(self, prompt: str, secret: bool = False) -> str:
        if self._ask_callback is None:
            raise RuntimeError("ask() called without an active connection callback")
        return await self._ask_callback(prompt, secret)

    def bind_ask_callback(
        self, callback: Callable[[str, bool], Awaitable[str]]
    ) -> None:
        self._ask_callback = callback

    def ok(self, data: object = "") -> Response:
        return Response(status=ResponseStatus.OK, data=data, exit_code=0)

    def err(self, message: str, exit_code: int = 1) -> Response:
        return Response(status=ResponseStatus.ERROR, data=message, exit_code=exit_code)


def _as_string_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(item) for item in value]
    return []


def _as_mapping(value: object) -> Mapping[str, object] | None:
    if isinstance(value, Mapping):
        return value
    return None


def _as_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def coerce_context(raw: Mapping[str, object]) -> Context:
    terminal = _as_mapping(raw.get("terminal"))
    if terminal is None:
        raise ValueError("missing required terminal metadata")

    user = _as_mapping(raw.get("user")) or {}
    flags_value = raw.get("flags")
    flags = dict(flags_value) if isinstance(flags_value, Mapping) else {}
    env_value = raw.get("env")
    env = dict(env_value) if isinstance(env_value, Mapping) else {}
    path = _as_string_list(raw.get("path", []))
    args = _as_string_list(raw.get("args", []))
    raw_color_depth = str(terminal.get("color_depth", "none"))
    if raw_color_depth == "16":
        color_depth: Literal["none", "16", "256", "truecolor"] = "16"
    elif raw_color_depth == "256":
        color_depth = "256"
    elif raw_color_depth == "truecolor":
        color_depth = "truecolor"
    else:
        color_depth = "none"

    return Context(
        path=path,
        args=args,
        flags=flags,
        cwd=str(raw.get("cwd", ".")),
        env={str(key): str(value) for key, value in env.items()},
        user=UserContext(
            name=str(user.get("name", "unknown")),
            id=_as_int(user.get("id")),
        ),
        terminal=TerminalContext(
            is_tty=bool(terminal.get("is_tty", False)),
            color_depth=color_depth,
            no_color=bool(terminal.get("no_color", True)),
        ),
        request_id=str(raw.get("request_id") or uuid4().hex),
        command_name=str(raw.get("command_name") or " ".join(path)),
        plugin_id=str(raw.get("plugin_id", "")),
    )
