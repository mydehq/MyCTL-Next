# Plugin Lifecycle

This page explains what happens to a plugin after discovery and before it becomes active in the daemon.

The lifecycle is a state machine with three important jobs:

- isolate plugin initialization
- reject broken plugins without crashing the daemon
- keep background tasks alive without killing the event loop

---

## 1. Lifecycle States

The daemon treats a plugin as moving through these states:

1. discovered
2. validated
3. dependency-synced
4. imported
5. initialized
6. active

If any step fails, the plugin stops moving forward and is rejected.

The daemon itself stays up.

---

## 2. Discovery And Validation

Discovery decides whether a plugin candidate should be considered.

Validation checks that the candidate is structurally safe to load.

The daemon verifies:

- the folder exists
- `pyproject.toml` exists
- the directory name matches `[project].name`
- the declared API compatibility is acceptable

This keeps invalid plugins out of the loader.

---

## 3. Dependency Sync

If a plugin declares dependencies, the daemon syncs them before import.

This step exists so plugin code can rely on its own declared runtime dependencies without mutating the daemon environment manually.

The plugin is not considered loaded until dependency sync succeeds.

---

## 4. Import And Registration

Once dependencies are ready, the daemon imports the plugin’s entry module in its own namespace.

That import does three things:

- executes top-level registration code
- attaches command and flag metadata from decorators
- prepares lifecycle hooks such as `on_load` and `periodic`

The important detail is that the plugin is still not active until initialization hooks finish.

---

## 5. On-Load Initialization

`on_load` hooks are the plugin’s startup check.

The daemon runs them sequentially so a failure in one hook can stop initialization immediately.

If a hook raises an exception, the plugin is rejected and its registration is rolled back.

That rollback keeps the plugin from appearing partially loaded in the runtime registry.

---

## 6. Active State

After successful initialization, the plugin becomes active.

At that point:

- command handlers remain in memory until dispatch time
- the registry can route requests to the plugin’s handlers
- periodic background jobs may run in the event loop

The plugin is now part of the daemon’s live command set.

---

## 7. Periodic Tasks

Periodic tasks are background loops managed by the daemon.

They are wrapped so that one failing iteration does not terminate the task permanently or crash the daemon.

The important behavior is:

- sleep between iterations
- execute the task
- catch and log exceptions
- continue the loop after failure

That makes periodic tasks resilient even when plugin code is noisy or unstable.

---

## 8. Failure Handling

Plugin failures are contained.

There are two common failure points:

- initialization failure during `on_load`
- runtime failure inside a periodic task

Initialization failure means the plugin is rejected.
Periodic task failure means the task logs the error and keeps looping.

The daemon should keep serving other plugins and commands either way.

---

## 9. What Lifecycle Does Not Do

Lifecycle does not handle:

- discovery tier scanning
- schema building
- command dispatch
- CLI rendering

Those concerns belong to discovery, registry, and client layers.

---

## 10. Summary

Plugin lifecycle is the part of the daemon that turns a validated importable plugin into an active runtime participant.

The flow is:

- discover
- validate
- sync dependencies
- import
- initialize
- activate

Failures are isolated to the plugin that caused them.
