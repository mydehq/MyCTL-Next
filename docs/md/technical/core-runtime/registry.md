# Core Engine & Registry

This page explains how MyCTL routes commands internally.

The registry is the daemon’s command router and schema source of truth. It does two jobs:

- resolve an incoming command path to the correct handler
- build the command tree that the client uses to render CLI help

The important part is that those two jobs are separate. Dispatch is for runtime. Schema is for client UI.

---

## 1. What The Registry Stores

At runtime the daemon keeps two command sources in memory:

- built-in daemon commands from `daemon/myctld/syscmds/`
- plugin commands discovered from loaded plugins

Built-in commands are registered through decorator metadata in `daemon/myctld/syscmds/registry.py`.
Plugin commands are registered through `myctl.api` metadata.

The registry does not care where the metadata came from. It only cares about the final normalized shape:

- command path
- help text
- flag metadata
- handler callable
- owning namespace

That makes the registry the shared runtime boundary between daemon internals and plugin code.

---

## 2. Command Tree Shape

The client-facing command tree is nested.

A path like `audio volume set` becomes a structure like this:

```python
{
    "audio": {
        "type": "group",
        "children": {
            "volume": {
                "type": "group",
                "children": {
                    "set": {
                        "type": "command",
                        "help": "Set volume",
                        "flags": [...],
                        "handler": <callable>,
                    }
                }
            }
        }
    }
}
```

That same shape is used for:

- daemon commands such as `status` and `schema`
- plugin commands such as `audio volume set`

The tree is built from metadata, not from hardcoded command lists.

---

## 3. Schema Building

Schema building now lives in `daemon/myctld/schema.py`.

The registry asks the builder to turn runtime command metadata into a JSON-serializable tree.

The builder is responsible for:

- splitting command paths into segments
- creating group nodes for intermediate segments
- attaching flag metadata to leaf commands
- combining built-in commands and plugin commands into one tree

The registry is only responsible for handing the builder the current runtime state.

This is why `schema()` is cheap to reason about:

- no dispatch logic
- no plugin lifecycle logic
- no path traversal logic beyond tree assembly

---

## 4. Dispatch Flow

Dispatch is the runtime fast path.

When a user runs a command, the daemon already has the request context, command path, and flag values. The registry then looks for the handler in this order:

1. built-in daemon commands
2. plugin command tree
3. fallback help or error response if nothing matches

For built-ins, the registry checks the longest matching path first. That means both single-word and nested daemon commands work:

- `status`
- `schema`
- `plugin reload`
- `sdk setup`

The dispatcher does not rebuild the schema during execution. It uses the stored runtime tables directly.

That keeps command execution focused on one job: find the handler and run it.

---

## 5. Built-In Commands

Built-in commands live in `daemon/myctld/syscmds/`.

The flow is:

- `daemon/myctld/syscmds/__init__.py` auto-imports command modules
- command decorators in `daemon/myctld/syscmds/api.py` attach metadata
- `daemon/myctld/syscmds/registry.py` stores the normalized handler information
- the registry reads that data during dispatch and schema generation

Built-ins are part of the daemon itself, so they can import `myctld` internals directly.

That means a built-in command can use:

- config helpers
- logging helpers
- plugin manager state
- IPC helpers
- runtime services

The internal command API exists to keep the authoring style clean, not to restrict access.

---

## 6. Plugin Commands

Plugins contribute to the same registry shape, but through the public SDK.

The plugin side still uses:

- `Plugin()`
- `@plugin.command(...)`
- `@plugin.flag(...)`
- `@plugin.flags([...])`
- `Context`
- `Response`

The registry sees plugin commands and built-in commands as the same kind of runtime object once they are normalized.

That is why the command tree can merge both sources without special cases in the client.

---

## 7. Flags

Flags are stored alongside the command they belong to.

That allows the registry to use the same metadata for:

- CLI help generation
- pre-validation
- request dispatch
- schema output

A leaf command node contains the command handler and its flags. A group node only contains children.

This is why commands like `plugin reload` or `logs --level info` can expose clean help text without the dispatcher needing to know command-specific parsing rules.

---

## 8. Why Schema And Dispatch Stay Separate

The original registry design mixed tree building and request execution. That made the code harder to understand and harder to test.

The current split is better because:

- schema building can be tested without live requests
- dispatch can be tested without rebuilding the tree
- changes to CLI structure do not affect runtime routing
- the registry module stays focused on orchestration

In practice, that means:

- `schema.py` answers: “what commands exist?”
- `registry.py` answers: “which handler should run now?”

---

## 9. What Happens On `myctl schema`

When the client asks for schema, the daemon:

1. collects built-in command metadata
2. collects plugin metadata
3. passes both into the schema builder
4. returns the merged tree to the client

The client then uses that tree to render help and inflate its command UI.

That is why schema generation is part of the runtime contract, not just a debugging feature.

---

## 10. What Happens On A Normal Command

When the client runs a real command, the daemon skips schema building and goes straight to routing.

Example flow:

1. client sends `myctl plugin reload audio`
2. daemon builds `Context`
3. registry resolves `plugin reload`
4. handler receives `ctx` and the runtime registry
5. handler returns a `Response`
6. daemon sends the normalized result back to the client

The registry does not need to inspect command source files at this point. It already has the registered metadata in memory.

---

## 11. Command Source Of Truth

The source of truth is the runtime metadata, not a manifest file and not a hand-written command table.

For built-ins, the metadata is attached through the syscommand decorators.
For plugins, the metadata is attached through the plugin SDK decorators.

That keeps the command system uniform without making built-ins behave like plugins at runtime.

---

## 12. Practical Mental Model

A useful way to think about the registry is:

- command modules define behavior
- decorators capture metadata
- the registry normalizes and stores that metadata
- schema builder renders the tree
- dispatcher executes the right handler

If you keep that split in mind, the implementation stays easy to reason about.

---

## 13. Summary

The registry is the daemon’s routing core.

It connects:

- built-in daemon commands
- plugin commands
- schema generation
- request dispatch

The design is intentionally simple: one metadata model, two runtimes, one router.
