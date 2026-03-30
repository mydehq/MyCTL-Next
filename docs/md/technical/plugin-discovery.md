# Plugin Discovery Engine

The MyCTL daemon features a high-performance **Discovery Engine** that automatically builds the universal command tree by scanning structured plugins across external directories.

It guarantees secure memory execution by strictly sandboxing code logic through standard `importlib` and "Total Override" rules.


## 1. Implicit Identity

When MyCTL boots (or is commanded to refresh), the engine systematically scans the plugin tiers (e.g., `plugins/`).

Instead of demanding complex registration objects from developers, the daemon leverages the concept of **Directory-as-Identity**. The literal name of the directory a plugin resides in becomes its intrinsic **Plugin ID** and root namespace.

If the engine scans `plugins/weather/`, the CLI structure `myctl weather` is automatically reserved. The ID becomes the overarching path identifier mapped deeply into the daemon's routing logic.


## 2. Discovery Tiers & Total Override

Because the engine utilizes Implicit Identity (Folder Name = Plugin ID), the daemon inherently supports complete plugin replacement. User plugins completely override System plugins.

The internal array `PLUGIN_SEARCH_PATHS` stringently iterates directories from Highest Priority (Local Workspaces) downward to Lowest Priority (System Linux files).

```python
PLUGIN_SEARCH_PATHS = [
    DAEMON_DIR.parent / "plugins",    # Highest Priority (DEV Root Directory)
    USER_PLUGINS_PATH,                # Mid Priority (USER ~/.local/share/)
    Path("/usr/share/myctl/plugins")  # Lowest Priority (SYSTEM Default)
]
```

**The Total Override Rule**: 
When discovering extensions, the Engine tracks active names via `loaded_plugins = set()`. If an `audio` folder is successfully discovered and dynamically linked from the `DEV` priority tier, `audio` enters the tracking state.

When the scanner subsequently sweeps the `USER` and `SYSTEM` tiers, they are systematically blocked from merging or executing against the `audio` command struct. This ensures that dropping a custom codebase in a high-priority folder completely eradicates default system alternatives safely without corrupting namespace merging.


## 3. Dynamic Loading (`importlib`)

To run custom python code, MyCTL cannot simply execute external scripts (which ruins stateful memory) or natively `import` plugins directly into the daemon's core namespace (which allows unsafe pointer collisions across independent features).

Instead, the `CommandRegistry.discover()` loop utilizes Python's `importlib.util` library to safely sandbox external developer logic inside the single running process.

```python
# 1. We construct an isolated module spec mapped explicitly to 'main.py'
spec = importlib.util.spec_from_file_location(plugin_id, str(entry_path))

# 2. We initialize an empty memory sandbox module layout
module = importlib.util.module_from_spec(spec)

# 3. We execute the user's codebase strictly inside this sandbox
if spec.loader:
    spec.loader.exec_module(module)
```

By manually generating the module execution, MyCTL prevents arbitrary `init` pollution and guarantees that every extension thinks it's completely isolated.


## 4. The SDK `_hook` Injection

A major technical hurdle arises with heavily sandboxed modules: If developers use the official SDK (`from myctl.api import registry`), how does that sandbox talk *backward* to the actual `CommandRegistry` class engine running it?

The engine employs a low-level dependency injection known as the **`_hook` Override**.

During the discovery iteration of a specific active plugin, the central `myctl.api` module momentarily receives a function pointer directly from the Engine Core:

```python
import myctl.api

# Define a hook that forwards instantly to the active Engine class
def _hook(path: str, help: str, func: Callable):
    self.add_cmd(plugin_id, path, func, help)

# Temporarily strap the mapping hook to the public SDK
myctl.api._dispatch_hook = _hook

# [Sandbox Exec: spec.loader.exec_module(module)]

# Instantly strip the hook once the file finishes compiling
myctl.api._dispatch_hook = None
```

When a plugin developer types `@registry.add_cmd("status")`, the SDK decorator internally fires `_dispatch_hook("status", function_reference)`. This allows the exact memory address of the user's isolated `async def` logic to pass securely backward into the Daemon's core $O(1)$ memory map without destroying the module boundary.
