"""
MyCTL IPC Management
Defines the standard request/response protocol for the Lean-Go / Fat-Python bridge.
"""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class Request(BaseModel):
    """
    Standard IPC Request Object.
    Sent by the Go proxy as a JSON packet.
    """

    path: list[str] = Field(default_factory=list, description="The hierarchical command path (e.g., ['audio', 'status'])")
    args: list[str] = Field(default_factory=list, description="Raw arguments passed to the final handler")
    flags: dict[str, Any] = Field(default_factory=dict, description="Pre-parsed flags and options")
    cwd: str = Field(default=".", description="The current working directory of the user")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables from the user")


class Response(BaseModel):
    """
    Standard IPC Response Object.
    Returned to the Go proxy for output and exit code control.
    """

    status: str = "ok"  # "ok" or "error"
    data: Any = ""
    exit_code: int = 0


# ── Factory Helpers ──────────────────────────────────────────────────────────

def ok(data: Any = "") -> dict:
    """Convenience helper for a successful response."""
    return Response(status="ok", data=data, exit_code=0).model_dump()


def err(message: str, exit_code: int = 1) -> dict:
    """Convenience helper for an error response."""
    return Response(status="error", data=message, exit_code=exit_code).model_dump()
