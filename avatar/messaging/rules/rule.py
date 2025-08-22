from typing import Type, Any,Tuple, Callable, Optional, Union
from dataclasses import dataclass
from ..stream import IMessage

@dataclass
class RuleConnector:
    type: Optional[Type] = None
    include_publisher_prefixes: tuple[str,...]|None = None
    exclude_publisher_prefixes: tuple[str,...]|None = None

    def check_incoming_internal(self, message_type: Type, publisher: str):
        if self.type is not None:
            if not issubclass(message_type, self.type):
                return False
        if self.exclude_publisher_prefixes is not None:
            for prefix in self.exclude_publisher_prefixes:
                if publisher.startswith(prefix):
                    return False
        if self.include_publisher_prefixes is not None:
            found = False
            for prefix in self.include_publisher_prefixes:
                if publisher.startswith(prefix):
                    found = True
                    break
            return found
        return True


    def check_incoming(self, message: IMessage):
        return self.check_incoming_internal(type(message), message.envelop.publisher)


@dataclass
class SyncCallSpec:
    argument_type: type
    returned_type: type

@dataclass
class Rule:
    name: str
    input: RuleConnector
    host_object: Any
    service: Callable
    asynchronous: bool
    outputs: Optional[Tuple[Type[IMessage], ...]]
    calls: Tuple[SyncCallSpec, ...]

    def __post_init__(self):
        if self.outputs is not None:
            if not isinstance(self.outputs, tuple):
                raise ValueError(f"outputs are expected to be tuple for the rule {self.name}, but were {self.outputs}")
            for index, element in enumerate(self.outputs):
                if not isinstance(element, type):
                    raise ValueError(f"outputs expected to by types, but at index #{index} was {element} for the rule {self.name}")

