from .type_handler import ITypeHandler, SerializationContext
from ..json_schema import JsonSchema
from typing import TypeVar, Any

class NoneHandler(ITypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is type(None):
            return NoneHandler()
        return None

    @property
    def python_type(self) -> type:
        return type(None)

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if value is not None:
            raise TypeError(f"Expected None at {context.current_path}, got {type(value)}")
        return None

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if json_value is not None:
            raise TypeError(f"Expected `null` at {context.current_path}, got {type(json_value)}")
        return None

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'null'}

