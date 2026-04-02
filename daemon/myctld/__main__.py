"""Process entrypoint for ``python -m myctld``.

This module is intentionally small: it optionally sets a friendly process
title, then delegates full runtime setup to ``myctld.app.main``.

It also enables postponed annotation evaluation for consistency with the rest
of the daemon package.

Read before: daemon/myctld/config.py; read after: daemon/myctld/__init__.py
"""

from __future__ import annotations

import asyncio

from .app import main
from .config import APP_NAME

try:
    from setproctitle import setproctitle
except Exception:
    setproctitle = None


if __name__ == "__main__":
    if setproctitle is not None:
        # Use canonical daemon name from config so behavior is deterministic.
        setproctitle(APP_NAME)
    # asyncio.run manages loop creation/teardown and propagates exit status.
    raise SystemExit(asyncio.run(main()))
