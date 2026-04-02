# Project Roadmap

This document tracks implementation status against the current MyCTL architecture.

## ✅ Current Baseline

- `myctld` daemon package is active (`daemon/myctld/`).
- Lean Go client proxies requests and inflates CLI from live daemon schema.
- Bootstrap path uses managed `uv sync` + deterministic venv launch.
- Readiness gate uses `__DAEMON_READY__` handshake.
- Daemon lifecycle supports graceful `stop`, signal shutdown, and socket cleanup.
- Default `myctl start` runs foreground daemon; `myctl start -b` runs background mode.
- Plugin SDK boundary is `myctl.api`; runtime internals remain in `myctld`.

## 🔧 In Progress

- Align docs/examples to current command surface (`status`, `start`, `stop`, `schema`, `logs`, `sdk`).
- Expand production simulation coverage for client command matrix and edge cases.
- Continue simplifying type scaffolding that does not improve runtime clarity.

## 📅 Next Steps

1. Implement richer daemon observability (request-id/command tags in emitted logs).
2. Add command-level regression tests for boot, stop/restart, and schema hydration.
3. Harden plugin loader error reporting and load-time diagnostics.
4. Document stable SDK surface guarantees for plugin authors.
5. Finalize the decorator-driven syscommands refactor plan and migration path.

## ✅ Verification Checklist

- Cold boot works from client command path.
- Foreground and background start modes both work.
- `stop` actually terminates daemon process.
- Signal shutdown prints a user-visible message and cleans socket.
- Schema hydration path remains functional after restart.
