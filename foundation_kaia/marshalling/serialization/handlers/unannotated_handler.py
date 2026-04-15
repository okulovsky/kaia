from __future__ import annotations
import base64
import pickle
from typing import Any, TypeVar

from .type_handler import ITypeHandler, SerializationContext
from ..json_schema import JsonSchema


class UnannotatedHandler(ITypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        return UnannotatedHandler()

    @property
    def python_type(self) -> type:
        return object

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        from .dataclass_handler import DataclassHandler
        from .sqlalchemy_handler import SqlalchemyHandler
        from .list_type_handler import ListHandler
        from .dict_type_handler import DictHandler
        from ..serializer import Serializer
        from ...reflector.annotation import Annotation

        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return ListHandler(Serializer(Annotation.default())).to_json(value, context)
        if isinstance(value, dict):
            return DictHandler(Serializer(Annotation.parse(str)), Serializer(Annotation.default())).to_json(value, context)
        if isinstance(value, bytes):
            from .bytes_handler import BytesHandler
            return BytesHandler().to_json(value, context)
        if DataclassHandler.is_eligible(value):
            return DataclassHandler(None).to_json(value, context)
        if SqlalchemyHandler.is_eligible(value):
            return SqlalchemyHandler(None).to_json(value, context)
        s = base64.b64encode(pickle.dumps(value)).decode('ascii')
        return {'@type': '@base64', '@content': s}

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        from .dataclass_handler import DataclassHandler
        from .sqlalchemy_handler import SqlalchemyHandler
        from .list_type_handler import ListHandler
        from .dict_type_handler import DictHandler
        from ..serializer import Serializer
        from ...reflector.annotation import Annotation

        if json_value is None or isinstance(json_value, (bool, int, float, str)):
            return json_value
        if isinstance(json_value, list):
            return ListHandler(Serializer(Annotation.default())).from_json(json_value, context)
        if isinstance(json_value, dict):
            type_tag = json_value.get('@type')
            if type_tag == DataclassHandler.type_token:
                return DataclassHandler(None).from_json(json_value, context)
            if type_tag == SqlalchemyHandler.type_token:
                return SqlalchemyHandler(None).from_json(json_value, context)
            if type_tag == 'bytes':
                from .bytes_handler import BytesHandler
                return BytesHandler().from_json(json_value, context)
            if type_tag == '@base64':
                return pickle.loads(base64.b64decode(json_value['@content']))
            return DictHandler(Serializer(Annotation.parse(str)), Serializer(Annotation.default())).from_json(json_value, context)
        raise TypeError(f"Cannot deserialize {type(json_value)} at {context.current_path}")

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {}
