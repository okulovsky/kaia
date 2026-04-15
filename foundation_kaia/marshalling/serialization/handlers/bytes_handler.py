import base64
from typing import Any, TypeVar

from .type_handler import ITypeHandler, SerializationContext
from ..json_schema import JsonSchema


class BytesHandler(ITypeHandler):
    TYPE_TAG = 'bytes'

    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if annotation is bytes:
            return BytesHandler()
        return None

    @property
    def python_type(self) -> type:
        return bytes

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, bytes):
            raise TypeError(f"Expected bytes at {context.current_path}, got {type(value)}")
        return {'@type': self.TYPE_TAG, 'value': base64.b64encode(value).decode('ascii')}

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, dict) or json_value.get('@type') != self.TYPE_TAG:
            raise TypeError(f"Expected {{'@type': '{self.TYPE_TAG}', 'value': ...}} at {context.current_path}")
        return base64.b64decode(json_value['value'])

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {
            'type': 'object',
            'properties': {
                '@type': {'const': self.TYPE_TAG},
                'value': {'type': 'string', 'contentEncoding': 'base64'},
            },
            'required': ['@type', 'value'],
        }
