from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any
from dataclasses import dataclass, field
from ..json_schema import JsonSchema

@dataclass
class SerializationContext:
    path: list = field(default_factory=list)
    allow_base64: bool = True

    @property
    def current_path(self) -> str:
        return '.'.join(str(c) for c in self.path)

    @contextmanager
    def subpath(self, segment):
        self.path.append(segment)
        try:
            yield self
        finally:
            self.path.pop()

class ITypeHandler(ABC):
    @property
    @abstractmethod
    def python_type(self) -> type:
        ...

    def assignable_to_type(self, python_type: type) -> bool:
        return python_type is self.python_type

    @abstractmethod
    def to_json(self, value: Any, context: SerializationContext) -> Any:
        ...

    @abstractmethod
    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        ...

    @abstractmethod
    def to_json_schema(self, root: JsonSchema) -> dict:
        ...



