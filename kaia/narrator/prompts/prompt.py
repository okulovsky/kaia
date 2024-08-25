from typing import *
from kaia.dub import Template, IPredefinedField
from dataclasses import dataclass

@dataclass
class PromptBinding:
    key: str|None
    function: Callable[[dict], Any]


class Prompt:
    def __init__(self, **kwargs):
        self._bindings: list[PromptBinding] = []
        for key, value in kwargs.items():
            self.add_binding(key, value)


    def add_binding(self,
                    key: str|IPredefinedField|None,
                    action: Callable[[dict], Any] | Template | dict
                    ) -> 'Prompt':
        if isinstance(key, IPredefinedField):
            str_key = key.get_name()
        elif isinstance(key, str) or key is None:
            str_key = key
        else:
            raise ValueError(f"Key has to be str or Predefined, but was {key}")

        if isinstance(action, Template):
            self._bindings.append(PromptBinding(str_key, action.to_str))
        elif callable(action):
            self._bindings.append(PromptBinding(str_key, action))
        else:
            raise ValueError(f"action has to be template or callable, but was {action}")
        return self

    def preview(self):
        return self.add_binding(None, print)



    def _compute(self, data: dict):
        last_value = None
        for binding in self._bindings:
            value = binding.function(data)
            if binding.key is not None:
                last_value = value
                data[binding.key] = value
        return data, last_value

    def compute(self, data: dict):
        return self._compute(data)[0]

    def compute_last_value(self, data: dict):
        return self._compute(data)[1]


