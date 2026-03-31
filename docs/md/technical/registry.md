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

### Dynamic CLI Rehydration

Because `self._commands` is essentially a JSON-compatible tree, the daemon can manifest its entire internal state via the `__sys_schema` command. The Go proxy fetches this JSON on every boot and uses it to "inflate" its Cobra CLI tree, ensuring the client and server are always in perfect sync without manual re-compilation.

---

## 2. Dispatch & Execution Flow

When a user executes `myctl audio volume set 50`, the Go proxy tokenizes the path and passes `["audio", "volume", "set"]` to the daemon over IPC.

The Registry executes the dispatch in two sub-millisecond steps:

1.  **Traversal**: The engine uses the tokenized array to recursively descend the `children` map.
2.  **Execution**: Once it reaches the leaf node (the `"command"` type), it captures the `handler` pointer and executes it.

```python
# Conceptual dispatch logic
current = self._commands[path[0]]
for segment in path[1:]:
    current = current["children"][segment]

# Await the execution of the isolated plugin logic
await current["handler"](request)
```

By strictly utilizing memory pointers rather than string-based evaluation, the core routing loop achieves native execution speed, moving from the network socket to the function logic in microseconds.
