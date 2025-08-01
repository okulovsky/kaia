import inspect
from typing import Type
from dataclasses import is_dataclass
from avatar.services import *
from avatar.messaging import *
from avatar.known_messages import *

def print_message_class_sources(base_cls: Type) -> None:
    seen = set()
    def _recurse(cls: Type) -> None:
        for sub in cls.__subclasses__():
            if sub in seen:
                continue
            seen.add(sub)
            try:
                src = inspect.getsource(sub)
            except (OSError, TypeError):
                src = f"# source not available for {sub.__name__}"
            print(f"\n# ---- Source for {sub.__name__} ----\n{src}")
            _recurse(sub)
    _recurse(base_cls)

print_message_class_sources(IMessage)