from typing import *
from .dub import Dub
from .constant_dub import ConstantDub
from dataclasses import dataclass

@dataclass(frozen=True)
class DubBinding:
    type: Dub
    name: Optional[str]
    produces_value: bool
    consumes_value: bool
    custom_getter: Optional[Callable[[Dict], Any]]

    def get_value_to_consume(self, d: Dict):
        if self.consumes_value:
            if self.custom_getter is None:
                return d[self.name]
            return self.custom_getter(d)
        return None

    def set_produced_value(self, value, d: Dict):
        if self.produces_value:
            d[self.name] = value

    @staticmethod
    def variable(type: Dub, name: str):
        return DubBinding(type, name, True, True, None)

    @staticmethod
    def constant(value: str):
        return DubBinding(ConstantDub(value), None, False, False, None)
