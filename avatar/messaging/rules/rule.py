from typing import Type, Any,Tuple, Callable, Optional, Union
from dataclasses import dataclass
from ..stream import IMessage

@dataclass
class RuleConnector:
    type: Optional[Type] = None
    include_publisher_prefixes: tuple[str,...]|None = None
    exclude_publisher_prefixes: tuple[str,...]|None = None

    def check_incoming_internal(self, message_type: Type, publisher: str) -> str|None:
        if self.type is not None:
            if not issubclass(message_type, self.type):
                return f"Expected {self.type}, was {message_type}"
        if self.exclude_publisher_prefixes is not None and publisher is not None:
            for prefix in self.exclude_publisher_prefixes:
                if publisher.startswith(prefix):
                    return f'Publisher {publisher} excluded by {prefix}'
        if self.include_publisher_prefixes is not None:
            found = False
            if publisher is not None:
                for prefix in self.include_publisher_prefixes:
                    if publisher.startswith(prefix):
                        found = True
                        break
            if not found:
                return f"Pushlisher {publisher} is not among {self.include_publisher_prefixes}"
        return None


    def check_incoming(self, message: IMessage) -> str|None:
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

