from typing import *
from .dub import Dub
from .constant_dub import ConstantDub
from dataclasses import dataclass
from abc import ABC,abstractmethod

class IDubBinding(ABC):
    @property
    @abstractmethod
    def type(self) -> Dub:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


    def set_name(self, name: str):
        pass

    @property
    @abstractmethod
    def produces_value(self) -> bool:
        pass


    @abstractmethod
    def get_consumed_keys(self) -> Tuple[str,...]:
        pass

    @property
    def consumes_value(self) -> bool:
        return len(self.get_consumed_keys()) > 0

    @abstractmethod
    def get_value_to_consume(self, d: Dict) -> Any:
        pass

    @abstractmethod
    def set_produced_value(self, value, d: Dict) -> None:
        pass

    @staticmethod
    def variable(type: Dub, name: str):
        return DubBinding(type, name, True, True, None)

    @staticmethod
    def constant(value: str):
        return DubBinding(ConstantDub(value), None, False, False, None)



class DubBinding(IDubBinding):
    def __init__(self,
                type: Dub,
                name: Optional[str],
                produces_value: bool,
                consumes_value: bool,
                custom_getter: Optional[Callable[[Dict], Any]],
                ):
        self._type = type
        self._name = name
        self._produces_value = produces_value
        self._consumes_value = consumes_value
        self._custom_getter = custom_getter

    @property
    def type(self) -> Dub:
        return self._type

    @property
    def name(self) -> str:
        return self._name

    @property
    def produces_value(self) -> bool:
        return self._produces_value


    def get_consumed_keys(self) -> Tuple[str,...]:
        if self._consumes_value:
            return (self._name,)
        else:
            return ()

    def get_value_to_consume(self, d: Dict):
        if self._consumes_value:
            if self._custom_getter is None:
                return d[self._name]
            return self._custom_getter(d)
        return None

    def set_produced_value(self, value, d: Dict):
        if self._produces_value:
            d[self._name] = value


