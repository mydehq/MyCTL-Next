"""Low-level NDJSON encode/decode helpers for daemon IPC.

The daemon and client exchange newline-delimited JSON frames over a Unix
socket. This module provides the smallest possible conversion layer between
wire payloads and typed runtime objects.

Using ``from __future__ import annotations`` keeps type hints deferred and
avoids eager evaluation costs during import.

Read before: daemon/myctld/config.py; read after: daemon/myctld/logging.py
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from myctl.api.context import Context, Response, coerce_context


def parse_request(line: str | bytes) -> dict[str, object]:
    """Parse one NDJSON request line into a JSON object."""
    # Stream readers return bytes while tests may pass strings directly.
    # Accepting both keeps the function easy to reuse.
    text = line.decode() if isinstance(line, bytes) else line
    payload = json.loads(text.strip())
    if not isinstance(payload, Mapping):
        raise ValueError("request payload must be a JSON object")
    return dict(payload)


def make_context(raw: Mapping[str, object]) -> Context:
    """Coerce raw request mapping into typed runtime Context."""
    return coerce_context(raw)


def encode_response(response: Response) -> bytes:
    """Encode one response object as a newline-terminated JSON payload."""
    # Keep payload explicit and stable so clients can parse without relying
    # on Python object serialization details.
    payload = {
        "status": int(response.status),
        "data": response.data,
        "exit_code": response.exit_code,
    }
    return json.dumps(payload, ensure_ascii=True).encode() + b"\n"
