from abc import abstractmethod
from .type_handler import ITypeHandler, SerializationContext
from ..json_schema import JsonSchema
from enum import Enum
from datetime import datetime
from typing import Any, TypeVar
from pathlib import Path


class IPrimitiveTypeHandler(ITypeHandler):
    @abstractmethod
    def to_string(self, value: Any, context: SerializationContext) -> str:
        ...

    @abstractmethod
    def from_string(self, string: str, context: SerializationContext) -> Any:
        ...


class IntHandler(IPrimitiveTypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is int:
            return IntHandler()
        return None

    @property
    def python_type(self) -> type:
        return int

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"Expected int at {context.current_path}, got {type(value)}")
        return value

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if isinstance(json_value, bool) or not isinstance(json_value, int):
            raise TypeError(f"Expected int at {context.current_path}, got {type(json_value)}")
        return json_value

    def to_string(self, value: Any, context: SerializationContext) -> str:
        return str(value)

    def from_string(self, string: str, context: SerializationContext) -> Any:
        return int(string)

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'integer'}


class FloatHandler(IPrimitiveTypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is float:
            return FloatHandler()
        return None

    @property
    def python_type(self) -> type:
        return float

    def assignable_to_type(self, python_type: type) -> bool:
        return python_type is float or python_type is int

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError(f"Expected float at {context.current_path}, got {type(value)}")
        return float(value)

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if isinstance(json_value, bool) or not isinstance(json_value, (int, float)):
            raise TypeError(f"Expected number at {context.current_path}, got {type(json_value)}")
        return float(json_value)

    def to_string(self, value: Any, context: SerializationContext) -> str:
        return str(float(value))

    def from_string(self, string: str, context: SerializationContext) -> Any:
        return float(string)

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'number'}


class StringHandler(IPrimitiveTypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is str:
            return StringHandler()
        return None

    @property
    def python_type(self) -> type:
        return str

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, str):
            raise TypeError(f"Expected str at {context.current_path}, got {type(value)}")
        return value

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, str):
            raise TypeError(f"Expected str at {context.current_path}, got {type(json_value)}")
        return json_value

    def to_string(self, value: Any, context: SerializationContext) -> str:
        if not isinstance(value, str):
            raise TypeError(f"Expected str at {context.current_path}, got {type(value)}")
        return value

    def from_string(self, string: str, context: SerializationContext) -> Any:
        return string

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'string'}


class BoolHandler(IPrimitiveTypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is bool:
            return BoolHandler()
        return None

    @property
    def python_type(self) -> type:
        return bool

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool at {context.current_path}, got {type(value)}")
        return value

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, bool):
            raise TypeError(f"Expected bool at {context.current_path}, got {type(json_value)}")
        return json_value

    def to_string(self, value: Any, context: SerializationContext) -> str:
        return str(value)

    def from_string(self, string: str, context: SerializationContext) -> Any:
        if string == 'True':
            return True
        if string == 'False':
            return False
        raise ValueError(f"Expected '@True' or '@False' at {context.current_path}, got '{string}'")

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'boolean'}


class EnumHandler(IPrimitiveTypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return EnumHandler(annotation)
        return None

    def __init__(self, enum_type: type[Enum]):
        self.enum_type = enum_type

    @property
    def python_type(self) -> type:
        return self.enum_type

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, self.enum_type):
            raise TypeError(f"Expected {self.enum_type} at {context.current_path}, got {type(value)}")
        return value.name

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        try:
            return self.enum_type[json_value]
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid value for {self.enum_type} at {context.current_path}: {json_value}") from e

    def to_string(self, value: Any, context: SerializationContext) -> str:
        return value.name

    def from_string(self, string: str, context: SerializationContext) -> Any:
        try:
            return self.enum_type[string]
        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid value for {self.enum_type} at {context.current_path}: '{string}'") from e

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'enum': [v.value for v in self.enum_type]}


class DateTimeHandler(IPrimitiveTypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is datetime:
            return DateTimeHandler()
        return None

    @property
    def python_type(self) -> type:
        return datetime

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, datetime):
            raise TypeError(f"Expected datetime at {context.current_path}, got {type(value)}")
        return value.isoformat()

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, str):
            raise TypeError(f"Expected ISO datetime string at {context.current_path}, got {type(json_value)}")
        return datetime.fromisoformat(json_value)

    def to_string(self, value: Any, context: SerializationContext) -> str:
        return value.isoformat()

    def from_string(self, string: str, context: SerializationContext) -> Any:
        return datetime.fromisoformat(string)

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'string', 'format': 'date-time'}


class PathHandler(IPrimitiveTypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is Path:
            return PathHandler()
        return None

    @property
    def python_type(self) -> type:
        return Path

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, Path):
            raise TypeError(f"Expected Path at {context.current_path}, got {type(value)}")
        return str(value)

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, str):
            raise TypeError(f"Expected Path string at {context.current_path}, got {type(json_value)}")
        return Path(json_value)

    def to_string(self, value: Any, context: SerializationContext) -> str:
        return str(value)

    def from_string(self, string: str, context: SerializationContext) -> Any:
        return Path(string)

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'string', 'format': 'path'}
