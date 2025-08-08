from typing import *
import importlib


def get_type_by_full_name(full_name: str) -> Type[Any]:
    module_name, type_name = full_name.rsplit('/')
    module = importlib.import_module(module_name)
    try:
        return getattr(module, type_name)
    except AttributeError:
        raise ImportError(f"Module '{module_name}' has no attribute '{type_name}'")

def get_full_name_by_type(_type: Type) -> str:
    return _type.__module__ + '/' + _type.__qualname__