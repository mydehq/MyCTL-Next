# Plugin Discovery: The Extension Engine

The MyCTL daemon features a high-performance **Discovery Engine** that automatically constructs the universal command tree by scanning structured plugins across a tiered hierarchy of directories.

## 1. Implicit Identity

MyCTL leverages the concept of **Directory-as-Identity**. Instead of requiring developers to register their plugins with a central configuration file, the literal name of the directory a plugin resides in becomes its intrinsic **Plugin ID** and root namespace.

For example, if the engine scans `plugins/weather/`, the CLI structure `myctl weather` is automatically reserved. This ID is used as the primary key for the daemon's $O(1)$ routing table.

---

## 2. Tiered Discovery & Total Override

The engine supports a tiered override system, allowing developers and users to shadow default system functionality without modifying core files.

### The Search Hierarchy

The `PLUGIN_SEARCH_PATHS` are iterated from highest to lowest priority:

1.  **DEV Tier**: `plugins/` (Local project workspace).
2.  **USER Tier**: `{{metadata.paths.plugins}}` (User-specific extensions).
3.  **SYSTEM Tier**: `/usr/share/myctl/plugins/` (System-wide defaults).

### The Total Override Rule (Shadowing)

When the engine iterates over `PLUGIN_SEARCH_PATHS`, it maintains a `loaded_plugins` set. If a Plugin ID is identified in a high-priority tier, it is added to this set. Subsequent tiers containing a folder with the exact same name are skipped entirely:

```python
loaded_plugins = set()

for root in PLUGIN_SEARCH_PATHS:
    for plugin_dir in root.iterdir():
        plugin_id = plugin_dir.name

        # Immediate skip if shadowing a lower tier
        if plugin_id in loaded_plugins:
            continue

        # ... logic ...
        loaded_plugins.add(plugin_id)
```

This strict shadowing ensures `O(1)` reasoning. Dropping a custom `audio` plugin into your local workspace completely eradicates the system-default `audio` namespace. There is zero risk of command collision or accidental merging between functionally distinct layers.

---

## 3. Sandboxed Dynamic Loading

To execute external code without polluting the daemon's core memory space, MyCTL uses Python's `importlib.util` to create isolated module sandboxes.

```python
# 1. Construct a module spec for the plugin entry point (main.py)
spec = importlib.util.spec_from_file_location(plugin_id, str(entry_path))

# 2. Initialize an isolated module object
module = importlib.util.module_from_spec(spec)

# 3. Execute the plugin code exclusively within this sandbox
if spec.loader:
    spec.loader.exec_module(module)
```

By manually orchestrating the module execution, MyCTL prevents `init` pollution and ensures that every extension is strictly isolated from its neighbors.

---

## 4. The SDK Bridge (`_dispatch_hook`)

A unique technical challenge exists: how do functions decorated with `@registry.add_cmd` inside a sandbox communicate back to the central `CommandRegistry`?

The engine employs a **Temporary Dispatch Hook**. During the loading cycle of a specific plugin, the central `myctl.api` module is briefly injected with a function pointer from the engine core:

1.  **Injection**: The Engine sets `myctl.api._dispatch_hook` to a local closure that knows the current `plugin_id`.
2.  **Execution**: The plugin's `main.py` is executed. The `@registry.add_cmd` decorator detects the hook and fires it.
3.  **Registration**: The hook passes the command path and the `async def` reference back to the central registry.
4.  **Cleansing**: Once the plugin is loaded, the hook is reset to `None` to prevent accidental registration from other modules.

This "Backward Injection" allows the exact memory address of the user's isolated logic to pass securely into the Daemon's routing map without breaching the module boundary.

---

## 5. Zero-Config SDK Availability (`.pth` Injection)

To ensure that `import myctl.api` always works—even for plugins with no external `$PATH` linkage—the Discovery Engine automatically injects a `.pth` file into the managed virtual environment's `site-packages` on every boot.

Before analyzing the plugin directories, the daemon executes:

```python
site_packages = next(VENV_PYTHON.parent.parent.glob("lib/python*/site-packages"), None)

if site_packages and site_packages.exists():
    pth_file = site_packages / "myctl_sdk.pth"

    if not pth_file.exists() or pth_file.read_text().strip() != str(DAEMON_DIR):
        pth_file.write_text(str(DAEMON_DIR) + "\n")
```

By linking the daemon's core `DAEMON_DIR` source into the venv, this provides:

- **Instant IDE Autocompletion**: The `myctl sdk setup` trick works correctly because the internal Python module paths resolve perfectly.
- **Fail-Safe Import**: Developers can utilize `from myctl.api import ...` seamlessly without relying on `setup.py` or system PYTHONPATH hacking.
