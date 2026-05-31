from __future__ import annotations
from typing import Any, TYPE_CHECKING
from ..reflector.annotation import Annotation
from ..reflector.declared_type import DeclaredTypeArgumentKind
from .handlers.type_handler import ITypeHandler, SerializationContext
from .handlers.primitive_type_handler import IPrimitiveTypeHandler
from .handlers.none_handler import NoneHandler
from .json_schema import JsonSchema
from .json_type import JSON

if TYPE_CHECKING:
    from ..reflector.declared_type import DeclaredType


def _build_handler(dt: 'DeclaredType') -> ITypeHandler:
    from .handlers.list_type_handler import ListHandler
    from .handlers.dict_type_handler import DictHandler
    from .handlers.primitive_type_handler import (
        BoolHandler, IntHandler, FloatHandler, StringHandler,
        DateTimeHandler, EnumHandler, PathHandler
    )
    from .handlers.dataclass_handler import DataclassHandler
    from .handlers.sqlalchemy_handler import SqlalchemyHandler
    from .handlers.unannotated_handler import UnannotatedHandler
    from .handlers.bytes_handler import BytesHandler

    if dt.kind == DeclaredTypeArgumentKind.generic_type:
        annotation = dt.mro[0].generic_type
        origin = dt.mro[0].type
    else:
        annotation = dt.mro[0].type
        origin = None
    type_map = dt.mro[0].type_map

    # Bool must come before Int (bool is a subclass of int)
    parsers = [
        ListHandler, DictHandler,
        NoneHandler, BoolHandler, IntHandler, FloatHandler, StringHandler,
        DateTimeHandler, EnumHandler, PathHandler,
        BytesHandler, DataclassHandler, SqlalchemyHandler,
        UnannotatedHandler,
    ]
    for parser_cls in parsers:
        result = parser_cls.parse(annotation, origin, type_map)
        if result is not None:
            return result
    raise ValueError(f"Cannot find handler for {dt}")


class Serializer:
    Context = SerializationContext

    def __init__(self, annotation: Annotation):
        from .handlers.json_handler import JSONHandler
        from .handlers.unannotated_handler import UnannotatedHandler
        self.annotation = annotation
        if annotation.raw_annotation is JSON:
            self._handlers: tuple[ITypeHandler,...] = (JSONHandler(),)
        elif annotation.not_annotated:
            self._handlers = (UnannotatedHandler(),)
        else:
            self._handlers = tuple(_build_handler(dt) for dt in annotation.types)
        self._nullable = False
        self._is_primitive = True
        self._is_primitive_or_nullable = True
        for h in self._handlers:
            if not isinstance(h, IPrimitiveTypeHandler):
                self._is_primitive = False
                if not isinstance(h, NoneHandler):
                    self._is_primitive_or_nullable = False
            if isinstance(h, NoneHandler):
                self._nullable = True



    @staticmethod
    def parse(annotation: Any, type_map=None) -> 'Serializer':
        return Serializer(Annotation.parse(annotation, type_map))

    @property
    def handlers(self) -> tuple[ITypeHandler,...]:
        return self._handlers

    @property
    def is_primitive(self) -> bool:
        return self._is_primitive

    @property
    def is_primitive_or_nullable(self) -> bool:
        return self._is_primitive_or_nullable

    @property
    def is_nullable(self) -> bool:
        return self._nullable

    def to_json(self, value: Any, ctx: SerializationContext|None = None) -> Any:
        if ctx is None:
            ctx = SerializationContext()
        if not self._handlers:
            return value
        last_error = None
        for h in self._handlers:
            try:
                return h.to_json(value, ctx)
            except (TypeError, ValueError) as e:
                last_error = e
        if last_error:
            raise last_error
        raise TypeError(f"No handler for {type(value)}")

    def from_json(self, json_value: Any, ctx: SerializationContext|None = None) -> Any:
        if ctx is None:
            ctx = SerializationContext()
        if not self._handlers:
            return json_value
        last_error = None
        for h in self._handlers:
            try:
                return h.from_json(json_value, ctx)
            except (TypeError, ValueError) as e:
                last_error = e
        if last_error:
            raise last_error
        raise TypeError(f"No handler could deserialize {json_value}")

    def to_string(self, value: Any, ctx: SerializationContext|None = None) -> str:
        if ctx is None:
            ctx = SerializationContext()
        for h in self._handlers:
            if isinstance(h, IPrimitiveTypeHandler):
                try:
                    return h.to_string(value, ctx)
                except (TypeError, ValueError):
                    pass
        raise TypeError(f"Not a primitive type: {type(value)}")

    def from_string(self, string: str, ctx: SerializationContext|None = None) -> Any:
        if ctx is None:
            ctx = SerializationContext()
        for h in self._handlers:
            if isinstance(h, IPrimitiveTypeHandler):
                return h.from_string(string, ctx)
        raise TypeError("No primitive handler available")

    def _schema_fragment(self, root: JsonSchema) -> dict:
        if len(self._handlers) == 1:
            return self._handlers[0].to_json_schema(root)
        return {'anyOf': [h.to_json_schema(root) for h in self._handlers]}

    def to_json_schema(self) -> JsonSchema:
        root = JsonSchema()
        root.schema = self._schema_fragment(root)
        return root
