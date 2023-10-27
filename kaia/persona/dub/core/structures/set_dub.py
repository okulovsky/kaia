from typing import *
from .dub import Dub, IRandomizableDub
from enum import Enum
from abc import ABC, abstractmethod
from yo_fluq_ds import Query
from numpy.random import RandomState


T = TypeVar('T')




class SetDub(Dub, IRandomizableDub, ABC, Generic[T]):
    def __init__(self, value_list, name: str, placeholder_value = None):
        self._value_list = value_list
        self._str_to_value = None
        if placeholder_value is None:
            self._placeholder_value = Query.dict(self.str_to_value()).argmin(lambda z: len(z.key)).value
        else:
            self._placeholder_value = placeholder_value
        self._name = name

    def get_name(self):
        return self._name

    def get_all_values(self):
        return list(self._value_list)

    def str_to_value(self):
        if self._str_to_value is None:
            self._str_to_value = {s: v for v in self.get_all_values() for s in self.to_all_strs(v)}
        return self._str_to_value

    @abstractmethod
    def to_str(self, value: T) -> str:
        pass

    def to_all_strs(self, value: T) -> Tuple[str,...]:
        return (self.to_str(value),)

    def get_placeholder_value(self):
        if self._placeholder_value is None:
            return self.get_random_value()
        else:
            return self._placeholder_value

    def get_random_value(self, random_state: Optional[RandomState] = RandomState()):
        index = random_state.randint(0, len(self._value_list))
        value = self._value_list[index]
        return value



class DictDub(SetDub[T]):
    def __init__(self, value_to_str: Dict[T, str], name: Optional[str] = None):
        self._value_to_str = value_to_str
        short_value = Query.dict(value_to_str).order_by(lambda z: z.value).first().key
        if name is None:
            name = '[Dictionary]' + ','.join(f'{key}={value}' for key, value in value_to_str.items())
        super().__init__(list(value_to_str), name, short_value)

    def to_str(self, value: T) -> str:
        return self._value_to_str[value]



class EnumDub(DictDub):
    def __init__(self, enum: Type[Enum]):
        dct = {}
        for enum_value in enum:
            dub = enum_value.name.replace('_',' ') #type: str
            value = enum_value.value
            dct[enum_value] = dub
        super().__init__(dct, str(enum))
