from typing import *
from abc import ABC, abstractmethod

class SlotInput(ABC):
    def validate(self, value) -> Any:
        pass


class BoolInput(SlotInput):
    def __init__(self, value_from: Optional[str] = None):
        self.value_from = value_from

    def validate(self, value) -> Any:
        if value in [True, False]:
            return value
        return None


class RangeInput(SlotInput):
    def __init__(self,
                 min,
                 max,
                 step = None,
                 type = None,
                 custom_validator: Optional[Callable[[Any], Union[bool,str]]] = None):
        self.min = min
        self.max = max
        self.step = step
        self.type = type
        self.custom_validator = custom_validator

    def validate(self, value) -> Any:
        if self.type is not None:
            value = self.type(value)
        if value <self.min:
            value = self.min
        if value>=self.max:
            value = self.max
        if self.type is not None:
            value = self.type(value)
        if self.custom_validator is not None:
            validation = self.custom_validator(value)
            if isinstance(validation, str):
                raise ValueError(validation)
            elif isinstance(validation, bool) and not validation:
                raise ValueError(f'Custom validator rejected value {value} without a specific reason')
        return value
        

