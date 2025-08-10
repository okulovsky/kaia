from typing import Type, Any,Tuple, Callable, Optional, Union
from dataclasses import dataclass
from ..stream import IMessage

@dataclass
class RuleConnector:
    type: Optional[Type] = None
    publisher: Optional[str] = None
    in_envelop: bool = False
    include_publisher_prefixes: tuple[str,...]|None = None
    exclude_publisher_prefixes: tuple[str,...]|None = None

    def check_incoming(self, message: IMessage):
        if self.type is not None:
            if not isinstance(message, self.type):
                return False
        if self.publisher is not None:
            if self.publisher != message.envelop.publisher:
                return False
        if self.exclude_publisher_prefixes is not None:
            for prefix in self.exclude_publisher_prefixes:
                if message.envelop.publisher.startswith(prefix):
                    return False
        if self.include_publisher_prefixes is not None:
            found = False
            for prefix in self.include_publisher_prefixes:
                if message.envelop.publisher.startswith(prefix):
                    found = True
                    break
            return found
        return True

@dataclass
class Rule:
    name: str
    input: RuleConnector
    host_object: Any
    service: Callable
    asynchronous: bool
    outputs: Optional[Tuple[Type[IMessage], ...]]

    def __post_init__(self):
        if self.outputs is not None:
            if not isinstance(self.outputs, tuple):
                raise ValueError(f"outputs are expected to be tuple for the rule {self.name}")
            for index, element in enumerate(self.outputs):
                if not isinstance(element, type):
                    raise ValueError(f"outputs expected to by types, but at index #{index} was {element} for the rule {self.name}")

