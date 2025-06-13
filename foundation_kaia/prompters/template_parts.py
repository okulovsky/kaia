from dataclasses import dataclass
from typing import *
from abc import ABC, abstractmethod
from .address_builder import AddressBuilderGC
from .address import Address
from .abstract_prompter import IPrompter
from .referrer import Referrer

class ITemplatePart(ABC):
    @abstractmethod
    def to_str(self, value: Any) -> str:
        pass

    @abstractmethod
    def to_readable_expression(self) -> str:
        pass

    @staticmethod
    def parse_gc(uid: str):
        address = AddressBuilderGC.find(AddressBuilderGC.Dimension.address, uid)
        if address is None:
            raise ValueError(f"Cannot find uid {uid} in the cache")
        if AddressBuilderGC.find(AddressBuilderGC.Dimension.subprompt, uid):
            return SubpromptPropagationTemplatePart(address)
        else:
            return AddressTemplatePart(
                address,
                AddressBuilderGC.find(AddressBuilderGC.Dimension.operator, uid),
                AddressBuilderGC.find(AddressBuilderGC.Dimension.misc, uid),
            )


@dataclass
class ConstantTemplatePart(ITemplatePart):
    value: str

    def to_str(self, value: Any) -> str:
        return self.value

    def to_readable_expression(self) -> str:
        return self.value

@dataclass
class AddressTemplatePart(ITemplatePart):
    address: Address
    formatter: Callable[[Any], str]|None = None
    misc: Any = None

    def to_str(self, value: Any) -> str:
        result = self.address.get(value)
        if self.formatter is not None:
            result = self.formatter(result)
        return str(result)

    def to_readable_expression(self) -> str:
        return '{{'+self.address.__str__()+'}}'

@dataclass
class SubpromptPropagationTemplatePart(ITemplatePart):
    address: Address

    def to_str(self, value: Any):
        return self.address.get(value)(value)

    def to_readable_expression(self) -> str:
        return '{{'+self.address.__str__()+"(_)}}"

