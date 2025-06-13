from typing import *
from ..core import CategoricalVariableDub, DubParameters
from enum import Enum

class OptionsDub(CategoricalVariableDub):
    def __init__(self,
                 options: Union[Dict[str, Any], Iterable[str], Type[Enum]]
                 ):
        self.value_to_strs: dict[Any,list[str]] = {}
        if isinstance(options, dict):
            for s, value in options.items():
                if value not in self.value_to_strs:
                    self.value_to_strs[value] = []
                self.value_to_strs[value].append(s)
        elif isinstance(options, type):
            for enum_value in options:
                dub = enum_value.name.replace('_', ' ')  # type: str
                value = enum_value.value
                if isinstance(value, str):
                    self.value_to_strs[enum_value] = [value]
                else:
                    self.value_to_strs[enum_value] = [dub]
        else:
            self.value_to_strs = {v:[v] for v in options}

    def get_values(self):
        return self.value_to_strs

    def value_to_all_strs(self, value, parameters: DubParameters, first_only: bool):
        for s in self.value_to_strs[value]:
            yield s

