from importlib import import_module
from types import ModuleType


def optional_import(module_name: str) -> ModuleType | None:
    try:
        return import_module(module_name)
    except ImportError:
        return None
