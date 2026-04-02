"""
MyCTL IPC Management
Defines the standard request/response protocol for the Lean-Go / Fat-Python bridge.
"""

from __future__ import annotations
from typing import Any, Callable, Awaitable
from pydantic import BaseModel, Field
from enum import IntEnum


class ResponseStatus(IntEnum):
    OK = 0
    ERROR = 1
    ASK = 2


class Response(BaseModel):
    """
    Standard IPC Response Object.
    Returned to the Go proxy for output and exit code control.
    """

    status: ResponseStatus = ResponseStatus.OK
    data: Any = ""
    exit_code: int = 0


class Context(BaseModel):
    """
    Standard IPC Context Object.
    Passed to plugin command handlers. Contains methods to send responses back.
    """

    path: list[str] = Field(
        default_factory=list,
        description="The hierarchical command path (e.g., ['audio', 'status'])",
    )
    args: list[str] = Field(
        default_factory=list, description="Raw arguments passed to the final handler"
    )
    flags: dict[str, Any] = Field(
        default_factory=dict, description="Pre-parsed flags and options"
    )
    cwd: str = Field(
        default=".", description="The current working directory of the user"
    )
    env: dict[str, str] = Field(
        default_factory=dict, description="Environment variables from the user"
    )
    plugin_id: str = Field(
        default="", description="The plugin namespace handling the command"
    )

    _ask_callback: Callable[[str, bool], Awaitable[str]] | None = None

    async def ask(self, prompt: str, secret: bool = False) -> str:
        """Prompt the user from the CLI and wait for a response.

        Args:
            prompt: Prompt text shown in the terminal.
            secret: If True, client input is masked when supported by the terminal.
        """
        if not hasattr(self, "_ask_callback") or not self._ask_callback:
            raise RuntimeError("ask() called without an active connection callback")
        return await self._ask_callback(prompt, secret)

    def ok(self, data: Any = "") -> Response:
        """Convenience helper for a successful response."""
        return Response(status=ResponseStatus.OK, data=data, exit_code=0)

    def err(self, message: str, exit_code: int = 1) -> Response:
        """Convenience helper for an error response."""
        return Response(status=ResponseStatus.ERROR, data=message, exit_code=exit_code)


def err(message: str, exit_code: int = 1) -> Response:
    return Response(status=ResponseStatus.ERROR, data=message, exit_code=exit_code)


def ok(data: Any = "") -> Response:
    return Response(status=ResponseStatus.OK, data=data, exit_code=0)
