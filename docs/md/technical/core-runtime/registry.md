# Command Registry: The O(1) Routing Engine

To maintain sub-millisecond execution times, the MyCTL daemon utilizes a specialized `CommandRegistry` that caches every available feature into an **$O(1)$ resolvable memory map**.

The registry acts as the central link between the isolated plugin sandboxes and the IPC server loop, holding direct references to Python function pointers for instant dispatch.

---

## 1. The N-Level Memory Tree

Command dispatch speed must be independent of its depth. Regular expressions or sequential string scanning are too expensive for a real-time system controller.

The `CommandRegistry` bypasses these costs by converting command paths (e.g., `audio volume set`) into a deeply nested Python dictionary structure during the discovery phase:

```python
self._commands = {
    "audio": {
        "type": "group",
        "help": "System audio controls",
        "children": {
            "volume": {
                "type": "group",
                "help": "Volume adjustment",
                "children": {
                    "set": {
                        "type": "command",
                        "help": "Set volume (0-100)",
                        "handler": <function_pointer_at_0x7f...>
                    }
                }
            }
        }
    }
}
```

This structural mapping guarantees that executing a 5-level deep command takes precisely the same amount of time as a top-level command.

Because the command tree is JSON-compatible, the daemon can manifest its internal state via the `schema` command. The Client fetches this JSON on boot and uses it to inflate its command tree.

### Tree Inflation Algorithm (`add_cmd`)

During the plugin discovery phase, each call to `@plugin.command` contributes metadata captured by the plugin instance. The registry iterates those handlers and invokes `CommandRegistry.add_cmd` to build the nested dictionary hierarchy incrementally, inserting nodes one at a time.

The algorithm works as follows:

1. **Ensure Root Group**: If the `plugin_id` (e.g., `"audio"`) does not yet have an entry in `self._commands`, a root group node is created.
2. **Tokenize Path**: The command path string (e.g., `"volume set"`) is split by whitespace into a list of segments: `["volume", "set"]`.
3. **Traverse and Grow**: The algorithm iterates over each segment, descending into the `children` map. If a segment does not exist, a new node is created:
   - **Intermediate segments** → create a `"group"` node with an empty `children` dict.
   - **Final segment** → create a `"command"` node with the resolved `help` string and the direct Python function pointer `handler`.
4. **Overwrite Prevention**: Because the check `if part not in current["children"]` is used, re-registering the same path is a no-op. The first registration wins. This is consistent with the Total Override Rule at the tier level.

```python
# Simplified trace: add_cmd("audio", "volume set", set_handler, "Set volume")
#
# Before: self._commands = {}
# After:
self._commands = {
    "audio": {
        "type": "group",
        "children": {
            "volume": {
                "type": "group",        # intermediate: created automatically
                "children": {
                    "set": {
                        "type": "command",
                        "handler": <set_handler>,
                        "help": "Set volume",
                    }
                }
            }
        }
    }
}
```

Group metadata (help text) is applied _after_ all `add_cmd` registrations during `discover()`, using the `groups` table from `pyproject.toml`'s `[tool.myctl]` section. This two-pass approach allows the manifest to document groups that may not yet exist when the plugin's `main.py` begins executing.

### Flag Metadata

Flags are registered alongside commands via the `@plugin.flag` decorator. The SDK normalizes these flags (adding prefixes, hyphenating names, and inferring types) before they are stored in the registry's command tree.

The `flags` list in a command node contains objects used by the system for:
1.  **Schema Generation**: The `schema` command exports these flags to the Go client for CLI generation.
2.  **Argparse Pre-parsing**: The `dispatch` method uses this metadata to construct an internal `argparse.ArgumentParser` that validates and extracts flag values from `ctx.args` before the handler is executed.

```python
# Internal flag metadata structure
{
    "name": "--output-format",
    "short": "-f",
    "type": "str",
    "default": "text",
    "required": False,
    "help": "Set output format"
}
```

---

## 2. Dispatch & Execution Flow

When a user executes `myctl audio volume set 50`, the Client tokenizes the path and passes `["audio", "volume", "set"]` to the daemon over IPC.

The Registry executes the dispatch in two sub-millisecond steps:

1.  **Traversal**: The engine uses the tokenized array to recursively descend the `children` map.
2.  **Execution**: Once it reaches the leaf node (the `"command"` type), it captures the `handler` pointer and executes it.

```python
# Conceptual dispatch logic
current = self._commands[path[0]]
for segment in path[1:]:
    current = current["children"][segment]

# Await the execution of the isolated plugin logic
await current["handler"](ctx)
```

By strictly utilizing memory pointers rather than string-based evaluation, the core routing loop achieves native execution speed, moving from the network socket to the function logic in microseconds.

### Path Resolution Strategy

The actual `dispatch` method in `CommandRegistry` has an important subtlety: it must determine not only _which_ handler to invoke, but also which portion of the context `path` array represents the command route vs. the user-supplied arguments.

The resolver uses an `args_start_idx` cursor that advances as each tree segment is matched:

```python
current = self._commands[plugin_id]    # Start at the plugin root node
args_start_idx = 1

for i in range(1, len(ctx.path)):
    part = ctx.path[i]
    if "children" in current and part in current["children"]:
        current = current["children"][part]  # Descend the tree
        args_start_idx = i + 1              # Advance cursor past matched segment
    else:
        break                               # Unknown segment = start of user args
```

After traversal, `ctx.args` is sliced from `args_start_idx` onward. This allows a command registered as `"volume set"` to correctly receive `["50"]` in its `ctx.args` when the user runs `myctl audio volume set 50`, even though the original `ctx.path` was `["audio", "volume", "set", "50"]`.

If traversal terminates on a `"group"` node (i.e., the user didn't provide a full command path), the daemon returns an `err()` response with the group's help text, which the Cobra client then renders as a formatted help page.
