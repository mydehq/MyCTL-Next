# Registry: Internal Engine Routing

The Python server acts as a continuously running async loop. To maintain sub-millisecond execution times, the daemon utilizes the `CommandRegistry` class to cache all available features into an $O(1)$ resolvable dictionary memory map.

The registry itself does not care *how* a command was registered (whether natively or via a sandboxed plugin)—its exclusive job is holding references to memory addresses and instantly routing incoming IPC network payloads to the correct Python function.

## 1. O(1) Memory Tree (`self._commands`)

Command dispatch must be instantaneous. Regular expressions or deep sequential string scanning are too expensive for a CLI proxy.

To resolve this, the `CommandRegistry` converts raw strings like `add_cmd("volume set")` into a deeply nested, N-dimensional Python `dict`:

```python
self._commands = {
    "audio": {
        "type": "group",
        "children": {
            "volume": {
                "type": "group",
                "children": {
                    "set": {
                        "type": "command",
                        "handler": <function memory_address>
                    }
                }
            }
        }
    }
}
```

This guarantees executing a 5-level deep command takes precisely the exact same sub-millisecond timeframe as executing a root command.

### Dynamic Tree Inflation (`schema`)
Because `self._commands` structurally matches a generic JSON topology (`group` vs `command`), the daemon can instantly walk this tree and dump it outwards over `.sock`. This is exactly how the `schema` system handler operates to rebuild the Cobra CLI automatically on the Go side.

## 2. Dispatch Mechanics

When the user runs `myctl audio volume set`, the Go proxy literally passes the tokenized array `["audio", "volume", "set"]` to Python over IPC.

The Daemon loop simply executes the array structurally:
1. `plugin_id = req.path[0]` (Extracts `"audio"`)
2. Traverses recursively through the `children` keys using loop iterators.

```python
current = self._commands[plugin_id]

# Lightning-fast constant-time key traversal
for part in req.path[1:]:
    current = current["children"][part]

# Await the execution of the final payload dictionary function pointer
await current["handler"](req)
```

By utilizing strict pointers to memory (`<function memory_address>`), the core routing loop achieves native execution speed without ever parsing domains, relying entirely on the memory dictionary graph compiled during the boot phase.
