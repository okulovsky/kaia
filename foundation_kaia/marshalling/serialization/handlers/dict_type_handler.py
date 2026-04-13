from __future__ import annotations
from typing import Any, TypeVar, get_args, TYPE_CHECKING

from .type_handler import ITypeHandler, SerializationContext
from .primitive_type_handler import IPrimitiveTypeHandler
from ..json_schema import JsonSchema
from ...reflector.annotation import Annotation
if TYPE_CHECKING:
    from ..serializer import Serializer


class DictHandler(ITypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if origin is not dict:
            return None
        from ..serializer import Serializer

        args = get_args(annotation)
        if args and len(args) == 2:
            key_ser = Serializer(Annotation.parse(args[0], type_map))
            val_ser = Serializer(Annotation.parse(args[1], type_map))
        else:
            key_ser = Serializer(Annotation.parse(str))
            val_ser = Serializer(Annotation.default())
        return DictHandler(key_ser, val_ser)

    def __init__(self, key_serializer: 'Serializer', value_serializer: 'Serializer'):
        if not key_serializer.is_primitive:
            raise TypeError(f"Dict key type must be primitive, got a non-primitive serializer")
        self.key_serializer = key_serializer
        self.value_serializer = value_serializer

    @property
    def python_type(self) -> type:
        return dict

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, dict):
            raise TypeError(f"Expected dict at {context.current_path}, got {type(value)}")
        result = {}
        for k, v in value.items():
            str_key = self.key_serializer.to_string(k, context)
            result[str_key] = self.value_serializer.to_json(v, context)
        return result

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, dict):
            raise TypeError(f"Expected dict at {context.current_path}, got {type(json_value)}")
        result = {}
        for str_key, v in json_value.items():
            with context.subpath(str_key):
                key = self.key_serializer.from_string(str_key, context)
                val = self.value_serializer.from_json(v, context)
            result[key] = val
        return result

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'object', 'additionalProperties': self.value_serializer._schema_fragment(root)}
