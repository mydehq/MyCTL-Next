from importlib import import_module
from pkgutil import iter_modules

from .registry import SYSTEM_COMMAND_HANDLERS, SYSTEM_COMMAND_HELP

# Keep registry tables referenced so the package exposes them intentionally.
REGISTRY_TABLES = (SYSTEM_COMMAND_HANDLERS, SYSTEM_COMMAND_HELP)


def _import_command_modules() -> None:
    for module_info in iter_modules(__path__):
        if module_info.name in {"registry", "core"} or module_info.name.startswith("_"):
            continue
        import_module(f"{__name__}.{module_info.name}")


_import_command_modules()
