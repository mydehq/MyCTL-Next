import sys
import subprocess
import tomllib
import importlib.util
import logging
import inspect
from pathlib import Path
from types import ModuleType
from typing import Callable, Any, Dict, List, Tuple

from .ipc import Context, Response, err, ok
from .config import PLUGIN_SEARCH_PATHS, API_VERSION, VENV_PYTHON, DAEMON_DIR
from myctl.api.logger import bind_logger_plugin, reset_logger_plugin


class CommandRegistry:
    def __init__(self):
        self._commands: Dict[
            str, Any
        ] = {}  # Nested Tree of Commands (Rooted by Plugin ID)
        self._plugins: Dict[str, Dict] = {}
        self.periodic_tasks: List[Tuple[int, Callable]] = []

        self._system_handlers: Dict[str, Callable] = {
            "__sys_schema": self._sys_schema,
            "__sys_version": self._sys_version,
            "__sys_logs": self._sys_logs,
            "ping": self._sys_ping,
            "version": self._sys_version,
            "--version": self._sys_version,
            "-v": self._sys_version,
            "ver": self._sys_version,
            "stop": self._sys_stop,
            "exit": self._sys_stop,
            "quit": self._sys_stop,
            "help": self._sys_help,
            "--help": self._sys_help,
            "-h": self._sys_help,
            "status": self._sys_status,
            "start": self._sys_start,
            "restart": self._sys_restart,
            "sdk": self._sys_sdk,
            "schema": self._sys_schema,
            "logs": self._sys_logs,
        }

        self._system_info = {
            "ping": "Health check (returns pong)",
            "version": "Display daemon and proxy versions",
            "stop": "Gracefully shut down the daemon",
            "status": "Show daemon runtime status (uptime, PID)",
            "start": "Ensure the daemon is running",
            "restart": "Restart the daemon process",
            "sdk": "IDE configuration and SDK management",
            "schema": "Dump the internal command hierarchy",
            "logs": "Show recent activity from the daemon logs",
            "daemon": "Native Engine Controller",
        }

    # ── System Handlers ──────────────────────────────────────────────────────

    async def _sys_schema(self, ctx: Context) -> Dict[str, Any]:
        """Provides the entire command hierarchy for the Go cli."""

        def serialize_node(node: Dict) -> Dict:
            out = {"type": node["type"], "help": node.get("help", "")}
            if "flags" in node and node["flags"]:
                out["flags"] = node["flags"]
            if "children" in node:
                out["children"] = {
                    k: serialize_node(v) for k, v in node["children"].items()
                }
            return out

        schema = {}

        # 1. Include System Handlers (Flattening aliases)
        for cmd_name, info in self._system_info.items():
            schema[cmd_name] = {
                "type": "command" if cmd_name != "daemon" else "group",
                "help": info,
            }
            if cmd_name == "daemon":
                schema[cmd_name]["children"] = {
                    "status": {"type": "command", "help": self._system_info["status"]},
                    "stop": {"type": "command", "help": self._system_info["stop"]},
                    "restart": {
                        "type": "command",
                        "help": self._system_info["restart"],
                    },
                    "start": {"type": "command", "help": self._system_info["start"]},
                    "logs": {"type": "command", "help": self._system_info["logs"]},
                }

        # 2. Include Loaded Plugins
        for p_id, data in self._commands.items():
            schema[p_id] = serialize_node(data)

        return ok(schema)

    async def _sys_sdk(self, ctx: Context) -> Dict[str, Any]:
        """Provides IDE configuration help and ensures SDK injection."""
        # 1. Ensure .pth is injected for SDK availability
        site_packages = (
            VENV_PYTHON.parent.parent
            / "lib"
            / f"python3.{sys.version_info.minor}"
            / "site-packages"
        )
        if site_packages.exists():
            pth_file = site_packages / "myctl_sdk.pth"
            pth_file.write_text(str(DAEMON_DIR) + "\n")

        return ok(
            {
                "message": "MyCTL SDK initialized.",
                "venv_python": str(VENV_PYTHON),
                "instruction": f"Point your IDE (VS Code/PyCharm) to use the following interpreter for autocompletion: {VENV_PYTHON}",
            }
        )

    async def _sys_start(self, ctx: Context) -> Dict[str, Any]:
        import time
        import sys

        current_time = time.time()
        main_module = sys.modules.get("__main__")
        boot_time = (
            getattr(main_module, "BOOT_TIME", current_time)
            if main_module
            else current_time
        )
        uptime = int(current_time - boot_time)

        if uptime < 5:
            return ok("Daemon started successfully.")
        return ok("Daemon is already running and operational.")

    async def _sys_restart(self, ctx: Context) -> Dict[str, Any]:
        import asyncio
        import sys

        loop = asyncio.get_running_loop()
        loop.call_later(0.1, sys.exit, 0)
        return ok("Daemon restarting...")

    async def _sys_ping(self, ctx: Context) -> Dict[str, Any]:
        return ok("pong")

    async def _sys_version(self, ctx: Context) -> Dict[str, Any]:
        from .config import APP_VERSION

        return ok(APP_VERSION)

    async def _sys_stop(self, ctx: Context) -> Dict[str, Any]:
        import asyncio
        import sys

        loop = asyncio.get_running_loop()
        loop.call_later(0.1, sys.exit, 0)
        return ok("Daemon shutting down...")

    async def _sys_help(self, ctx: Context) -> Dict[str, Any]:
        help_text = [
            "MyCTL - Desktop Controller",
            "Usage: myctl <plugin> <command> [args]",
            "",
            "Registered Plugins:",
        ]
        for p_id in sorted(self._commands.keys()):
            # Just listing the plugins for the fallback text help
            help_text.append(f"  - {p_id}: {self._commands[p_id].get('help', '')}")
        return ok("\n".join(help_text))

    async def _sys_logs(self, ctx: Context) -> Dict[str, Any]:
        """Returns the tail end of the daemon logs."""
        from .config import LOG_FILE

        if not LOG_FILE.exists():
            return ok("No log file found.")

        try:
            # Efficiently read the last 30 lines
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                tail = lines[-30:] if len(lines) > 30 else lines
                return ok("".join(tail).strip())
        except Exception as e:
            return err(f"Failed to read logs: {e}")

    async def _sys_status(self, ctx: Context) -> Dict[str, Any]:
        import time
        import os
        from .config import APP_VERSION

        current_time = time.time()
        import sys

        main_module = sys.modules.get("__main__")
        boot_time = (
            getattr(main_module, "BOOT_TIME", current_time)
            if main_module
            else current_time
        )
        uptime_seconds = int(current_time - boot_time)

        output = (
            f"MyCTL Daemon\n"
            f"  Status:   online\n"
            f"  Version:  {APP_VERSION}\n"
            f"  PID:      {os.getpid()}\n"
            f"  Uptime:   {uptime_seconds}s"
        )
        return ok(output)

    def add_cmd(
        self,
        plugin_id: str,
        path: str,
        handler: Callable,
        help: str = "",
        flags: list = None,
    ):
        """Helper to insert a command into the nested hierarchy."""
        if plugin_id not in self._commands:
            self._commands[plugin_id] = {
                "type": "group",
                "help": f"Main commands for plugin '{plugin_id}'",
                "children": {},
            }

        parts = path.strip("/").split()
        current = self._commands[plugin_id]

        # Traverse to the last part
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1

            if part not in current["children"]:
                if is_last:
                    current["children"][part] = {
                        "type": "command",
                        "help": help or handler.__doc__ or "",
                        "handler": handler,
                        "flags": flags or [],
                    }
                else:
                    current["children"][part] = {
                        "type": "group",
                        "help": f"Sub-group: {part}",
                        "children": {},
                    }

            current = current["children"][part]

    def _ensure_package(self, name: str, package_path: Path):
        """Ensure a namespace/package module exists in sys.modules."""
        if name in sys.modules:
            pkg = sys.modules[name]
            if not hasattr(pkg, "__path__"):
                pkg.__path__ = []
            if str(package_path) not in pkg.__path__:
                pkg.__path__.append(str(package_path))
            return

        pkg = ModuleType(name)
        pkg.__path__ = [str(package_path)]
        pkg.__package__ = name
        sys.modules[name] = pkg

    async def discover(self):
        """Tiers: DEV -> USER -> SYSTEM (Highest Priority wins entirely)"""

        # Ensure .pth is injected for SDK availability
        site_packages = next(
            VENV_PYTHON.parent.parent.glob("lib/python*/site-packages"), None
        )
        if site_packages and site_packages.exists():
            pth_file = site_packages / "myctl_sdk.pth"
            if not pth_file.exists() or pth_file.read_text().strip() != str(DAEMON_DIR):
                pth_file.write_text(str(DAEMON_DIR) + "\n")

        paths = PLUGIN_SEARCH_PATHS
        loaded_plugins = set()

        for root in paths:
            logging.info(f"Scanning for plugins in: {root}")
            if not root.exists():
                continue

            for plugin_dir in root.iterdir():
                if not plugin_dir.is_dir():
                    continue

                plugin_id = plugin_dir.name

                # If a higher tier already loaded this plugin, skip it entirely
                if plugin_id in loaded_plugins:
                    continue

                manifest_path = plugin_dir / "pyproject.toml"
                entry_path = plugin_dir / "main.py"  # fallback default

                if not manifest_path.exists():
                    continue

                try:
                    # 1. Read pyproject.toml manifest
                    with open(manifest_path, "rb") as f:
                        raw = tomllib.load(f)

                    project = raw.get("project", {})
                    myctl_meta = raw.get("tool", {}).get("myctl", {})

                    # Resolve the actual entry point (default: main.py)
                    entry_name = myctl_meta.get("entry", "main.py")
                    entry_path = plugin_dir / entry_name

                    if not entry_path.exists():
                        logging.warning(
                            f"Plugin '{plugin_id}' skipped: entry '{entry_name}' not found."
                        )
                        continue

                    # Enforce: [project].name must match the directory name
                    declared_name = project.get("name", "")
                    if declared_name != plugin_id:
                        logging.warning(
                            f"Plugin '{plugin_id}' skipped: [project].name '{declared_name}' "
                            f"must match the directory name '{plugin_id}'."
                        )
                        continue

                    # Flatten into a unified manifest dict for internal use
                    manifest = {
                        "name": plugin_id,
                        "version": project.get("version", "0.0.0"),
                        "info": project.get("description", ""),
                        "api_version": myctl_meta.get("api_version", "1.0.0"),
                        "dependencies": project.get("dependencies", []),
                        "groups": myctl_meta.get("groups", {}),
                    }

                    # Basic Semantic Version Check (Major version match)
                    plugin_api_v = manifest.get("api_version", "1.0.0").split(".")[0]
                    engine_api_v = API_VERSION.split(".")[0]

                    if plugin_api_v != engine_api_v:
                        logging.warning(
                            f"Plugin '{plugin_id}' skipped: API version mismatch. Expected v{engine_api_v}, got v{plugin_api_v}"
                        )
                        continue

                    self._plugins[plugin_id] = manifest

                    # 2. Install plugin dependencies via uv (reads plugin's pyproject.toml directly)
                    plugin_deps = manifest.get("dependencies", [])
                    if plugin_deps:
                        logging.info(
                            f"Plugin '{plugin_id}': syncing dependencies via uv..."
                        )
                        try:
                            result = subprocess.run(
                                [
                                    "uv",
                                    "pip",
                                    "install",
                                    "--quiet",
                                    "--python",
                                    str(VENV_PYTHON),
                                    str(
                                        plugin_dir
                                    ),  # uv reads pyproject.toml from plugin dir
                                ],
                                capture_output=True,
                                text=True,
                                timeout=120,
                            )
                            if result.returncode != 0:
                                logging.warning(
                                    f"Plugin '{plugin_id}': uv install failed:\n{result.stderr.strip()}"
                                )
                            else:
                                logging.info(
                                    f"Plugin '{plugin_id}': dependencies ready."
                                )
                        except subprocess.TimeoutExpired:
                            logging.warning(
                                f"Plugin '{plugin_id}': uv install timed out."
                            )
                        except FileNotFoundError:
                            logging.warning(
                                f"Plugin '{plugin_id}': 'uv' not found. "
                                "Skipping dependency installation."
                            )

                    # 3. Dynamic Import via package-context namespace
                    # Load each plugin under `myctl_plugins.<plugin_id>.*` to make
                    # relative imports deterministic and collision-free.
                    namespace_root = "myctl_plugins"
                    plugin_pkg = f"{namespace_root}.{plugin_id}"
                    entry_stem = entry_path.stem
                    entry_mod_name = f"{plugin_pkg}.{entry_stem}"

                    self._ensure_package(namespace_root, plugin_dir.parent)
                    self._ensure_package(plugin_pkg, plugin_dir)

                    spec = importlib.util.spec_from_file_location(
                        entry_mod_name,
                        str(entry_path),
                    )
                    if not spec or not spec.loader:
                        logging.error(
                            f"Plugin '{plugin_id}': Failed to create module spec."
                        )
                        continue

                    module = importlib.util.module_from_spec(spec)
                    sys.modules[entry_mod_name] = module

                    # Execute the module
                    try:
                        spec.loader.exec_module(module)
                    except Exception as e:
                        logging.error(
                            f"Plugin '{plugin_id}': Failed to execute module: {e}"
                        )
                        continue

                    # 4. Extract Plugin instance and register commands
                    plugin_instance = None
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        # Check if it's a Plugin instance with matching name
                        if (
                            hasattr(attr, "__class__")
                            and attr.__class__.__name__ == "Plugin"
                            and hasattr(attr, "name")
                            and attr.name == plugin_id
                        ):
                            plugin_instance = attr
                            break

                    if not plugin_instance:
                        logging.warning(
                            f"Plugin '{plugin_id}': No Plugin instance found with name '{plugin_id}'"
                        )
                        continue

                    # 5. Register commands from plugin._commands
                    if hasattr(plugin_instance, "_commands"):
                        for handler in plugin_instance._commands:
                            cmd_meta = getattr(handler, "__myctl_cmd__", {})
                            flags_meta = getattr(handler, "__myctl_flags__", [])
                            if "path" in cmd_meta:
                                self.add_cmd(
                                    plugin_id,
                                    cmd_meta["path"],
                                    handler,
                                    cmd_meta.get("help", ""),
                                    flags_meta,
                                )

                    # Apply root group description from [project].description
                    if plugin_id in self._commands:
                        self._commands[plugin_id]["help"] = (
                            manifest["info"] or f"Plugin '{plugin_id}'"
                        )

                    # Apply sub-group descriptions from [tool.myctl.groups]
                    for group_path, group_help in manifest["groups"].items():
                        if not group_path or plugin_id not in self._commands:
                            continue
                        parts = group_path.strip().split()
                        current = self._commands[plugin_id]
                        for part in parts:
                            children = current.setdefault("children", {})
                            if part not in children:
                                children[part] = {
                                    "type": "group",
                                    "help": "",
                                    "children": {},
                                }
                            current = children[part]
                        current["help"] = group_help

                    # 6. Run on_load lifecycle hooks
                    import asyncio

                    plugin_failed = False
                    if hasattr(plugin_instance, "_load_hooks"):
                        for hook in plugin_instance._load_hooks:
                            try:
                                hook_ctx = Context(
                                    path=[plugin_id], plugin_id=plugin_id
                                )
                                token = bind_logger_plugin(plugin_id)
                                try:
                                    takes_ctx = (
                                        len(inspect.signature(hook).parameters) > 0
                                    )
                                    if asyncio.iscoroutinefunction(hook):
                                        await (hook(hook_ctx) if takes_ctx else hook())
                                    else:
                                        hook(hook_ctx) if takes_ctx else hook()
                                finally:
                                    reset_logger_plugin(token)
                            except Exception as e:
                                logging.error(
                                    f"Plugin '{plugin_id}' critical initialization failure: {e}"
                                )
                                plugin_failed = True
                                break

                    if plugin_failed:
                        logging.critical(
                            f"REJECTED plugin '{plugin_id}': Failed initialization. Rolling back."
                        )
                        # Roll back registrations
                        if plugin_id in self._commands:
                            del self._commands[plugin_id]
                        if plugin_id in self._plugins:
                            del self._plugins[plugin_id]
                    else:
                        # 7. Process Background Tasks
                        if hasattr(plugin_instance, "_periodic_hooks"):
                            for interval, hook in plugin_instance._periodic_hooks:
                                hook_takes_ctx = (
                                    len(inspect.signature(hook).parameters) > 0
                                )

                                if inspect.iscoroutinefunction(hook):

                                    async def wrapped_async(
                                        fn=hook,
                                        pid=plugin_id,
                                        with_ctx=hook_takes_ctx,
                                    ):
                                        token = bind_logger_plugin(pid)
                                        try:
                                            if with_ctx:
                                                await fn(
                                                    Context(path=[pid], plugin_id=pid)
                                                )
                                            else:
                                                await fn()
                                        finally:
                                            reset_logger_plugin(token)

                                    self.periodic_tasks.append(
                                        (interval, wrapped_async)
                                    )
                                else:

                                    def wrapped_sync(
                                        fn=hook,
                                        pid=plugin_id,
                                        with_ctx=hook_takes_ctx,
                                    ):
                                        token = bind_logger_plugin(pid)
                                        try:
                                            if with_ctx:
                                                fn(Context(path=[pid], plugin_id=pid))
                                            else:
                                                fn()
                                        finally:
                                            reset_logger_plugin(token)

                                    self.periodic_tasks.append((interval, wrapped_sync))

                        logging.info(
                            f"Loaded plugin '{plugin_id}' (v{manifest.get('version', 'unknown')})"
                        )
                        loaded_plugins.add(plugin_id)

                except Exception as e:
                    logging.error(f"Error loading plugin '{plugin_id}': {e}")
                    continue

    async def dispatch(self, ctx: Context) -> Response:
        """Resolve System Handler or dispatch to Plugin"""
        if not ctx.path:
            return await self._sys_help(ctx)

        # ── 1. Check Native System Handlers ──────────────
        root_cmd = ctx.path[0]

        # Handle 'daemon <action>' syntax gracefully mapping to system handlers
        if root_cmd == "daemon" and len(ctx.path) >= 2:
            action = ctx.path[1]
            if action in ("stop", "status"):
                root_cmd = action
            elif action == "start":
                return await self._sys_start(ctx)
            elif action == "logs":
                return await self._sys_logs(ctx)
            elif action == "restart":
                return await self._sys_restart(ctx)

        if root_cmd in self._system_handlers:
            try:
                return await self._system_handlers[root_cmd](ctx)
            except Exception as e:
                return err(f"System Handler Error: {str(e)}")

        # ── 2. Standard Plugin Dispatch ──────────────────
        plugin_id = ctx.path[0]
        args_start_idx = 1

        if plugin_id not in self._commands:
            return err(f"Plugin ID '{plugin_id}' not found")

        current = self._commands[plugin_id]

        # Traverse the tree based on the provided path
        for i in range(1, len(ctx.path)):
            part = ctx.path[i]
            if "children" in current and part in current["children"]:
                current = current["children"][part]
                args_start_idx = i + 1
            else:
                break

        if current["type"] == "group":
            return err(f"Incomplete command. {current.get('help', '')}")

        handler = current.get("handler")
        if not handler:
            return err("No handler defined for this command path.")

        # Prune the handled path parts out of ctx.args
        ctx.args = (
            ctx.args[len(ctx.path) :]
            if len(ctx.args) >= len(ctx.path)
            else ctx.args[args_start_idx - 1 :]
        )

        # ── Pre-parse Declarative Flags ──────────────────
        flags_meta = current.get("flags", [])
        if flags_meta:
            import argparse

            class SilentParser(argparse.ArgumentParser):
                def error(self, message):
                    raise ValueError(message)

            parser = SilentParser(add_help=False)
            for fm in flags_meta:
                kwargs = {
                    "default": fm["default"],
                    "help": fm["help"],
                    "required": fm["required"],
                }

                if fm.get("choices"):
                    kwargs["choices"] = fm["choices"]

                t = fm.get("type", "str")
                if t == "bool":
                    kwargs.pop("type", None)
                    kwargs.pop("choices", None)
                    if fm["default"] is True:
                        kwargs["action"] = "store_false"
                    else:
                        kwargs["action"] = "store_true"
                elif t == "int":
                    kwargs["type"] = int
                elif t == "float":
                    kwargs["type"] = float
                else:
                    kwargs["type"] = str

                args_names = [fm["name"]]
                if fm.get("short"):
                    args_names.insert(0, fm["short"])

                parser.add_argument(*args_names, **kwargs)

            try:
                parsed, remaining = parser.parse_known_args(ctx.args)
                ctx.flags = vars(parsed)
                ctx.args = remaining
            except ValueError as ve:
                return err(f"Flag Error: {str(ve)}", exit_code=2)

        # ── Inject plugin_id into Context and dispatch ──────────────────
        ctx.plugin_id = plugin_id

        try:
            token = bind_logger_plugin(plugin_id)
            try:
                result = await handler(ctx)
            finally:
                reset_logger_plugin(token)
            if not isinstance(result, Response):
                logging.warning(
                    f"Plugin '{plugin_id}' handler at '{ctx.path}' returned invalid object: {type(result)}"
                )
                return err(
                    "Internal Error: Handler did not return a valid response object.\n"
                    "Did you forget to use ok() or err()?"
                )
            return result
        except Exception as e:
            return err(f"Handler Error: {str(e)}")
