# N-Level Command Discovery

The MyCTL command system is designed for **infinite hierarchical depth**. Unlike traditional CLI tools with flat structures, MyCTL represents commands as a recursive tree.

## The Registry Structure

Behind the scenes, the Python daemon maintains a nested dictionary of commands and namespaces.

```python
# A Simplified Conceptual Visualization
COMMAND_REGISTRY = {
    "audio": {
        "status": {"_fn": get_status, "_info": "Show audio stats"},
        "sink": {
            "mute": {"_fn": mute_sink, "_info": "Mute current output"}
        }
    },
    "ping": {"_fn": pong_handler, "_info": "Test socket health"}
}
```

### Path-Based Decoration
To register a command, you don't need to manually touch the registry. You use the namespaced `@registry.add_cmd` decorator:

- `@registry.add_cmd("audio status")` -> Adds `status` to the `audio` namespace.
- `@registry.add_cmd("audio sink mute")` -> Automatically builds the `audio` -> `sink` hierarchy.

## User Plugin Discovery

MyCTL automatically scans your **XDG Data Home** for additional functionality:
`~/.local/share/myctl/plugins/`

For every folder in this directory:
1.  **Loader Phase**: The daemon looks for `plugin.py`.
2.  **Mounting**: It dynamically imports the module.
3.  **Registration**: Any `@registry.add_cmd` calls inside the plugin are executed, injecting the new commands directly into the global command tree.

## Why this is Pro-Grade

### 1. Zero-Gap Proxying
Since the Go client just sends a raw list of strings (`["audio", "sink", "mute"]`), it doesn't need to know the structure of the registry. The Python side splits the list and "walks" the dictionary to find the leaf-node handler.

### 2. Native CLI Help
When you run `myctl help [path]`, the Python daemon recursively walks its own registry, calculates all valid sub-commands, and generates a formatted help menu—delivering a Cobra-like experience without the Cobra overhead.

### 3. Infinite Scalability
You can nest commands as deep as you'd like (e.g., `myctl system network vpn wg toggle`) and the system handles the routing in logarithmic time.
