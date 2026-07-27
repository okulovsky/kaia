from .primitive_type_handler import IPrimitiveTypeHandler
from .type_handler import SerializationContext
from ..json_schema import JsonSchema
from ..tools import TypeTools
from typing import TypeVar, Any


class TypeHandler(IPrimitiveTypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is type:
            return TypeHandler()
        return None

    @property
    def python_type(self) -> type:
        return type

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, type):
            raise TypeError(f"Expected type at {context.current_path}, got {type(value)}")
        return TypeTools.type_to_full_name(value)

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, str):
            raise TypeError(f"Expected type name string at {context.current_path}, got {type(json_value)}")
        return TypeTools.full_name_to_type(json_value)

    def to_string(self, value: Any, context: SerializationContext) -> str:
        return TypeTools.type_to_full_name(value)

    def from_string(self, string: str, context: SerializationContext) -> Any:
        return TypeTools.full_name_to_type(string)

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'string'}
