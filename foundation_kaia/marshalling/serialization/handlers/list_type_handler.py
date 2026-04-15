from __future__ import annotations
from ...reflector.annotation import Annotation
from .type_handler import ITypeHandler, SerializationContext
from ..json_schema import JsonSchema
from typing import Any, TypeVar, get_args, TYPE_CHECKING

if TYPE_CHECKING:
    from ..serializer import Serializer


class ListHandler(ITypeHandler):
    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        from ..serializer import Serializer

        if origin is list:
            args = get_args(annotation)
            element_ann = Annotation.parse(args[0], type_map) if args else Annotation.default()
            return ListHandler(Serializer(element_ann))
        if origin is tuple:
            args = get_args(annotation)
            if args:
                if len(args) == 2 and args[1] is Ellipsis:
                    element_ann = Annotation.parse(args[0], type_map)
                else:
                    # Fixed-length tuple: merge all types into one annotation
                    all_types = []
                    for arg in args:
                        all_types.extend(Annotation.parse(arg, type_map).types)
                    element_ann = Annotation(tuple(all_types), annotation)
            else:
                element_ann = Annotation.default()
            return ListHandler(Serializer(element_ann), as_tuple=True)
        return None

    def __init__(self, element_serializer: 'Serializer', as_tuple: bool = False):
        self.element_serializer = element_serializer
        self.as_tuple = as_tuple

    @property
    def python_type(self) -> type:
        return tuple if self.as_tuple else list

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if not isinstance(value, (list, tuple)):
            raise TypeError(f"Expected list/tuple at {context.current_path}, got {type(value)}")
        result = []
        for index, element in enumerate(value):
            with context.subpath(index):
                result.append(self.element_serializer.to_json(element, context))
        return result

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, list):
            raise TypeError(f"Expected list at {context.current_path}, got {type(json_value)}")
        result = []
        for index, element in enumerate(json_value):
            with context.subpath(index):
                result.append(self.element_serializer.from_json(element, context))
        if self.as_tuple:
            return tuple(result)
        return result

    def to_json_schema(self, root: JsonSchema) -> dict:
        return {'type': 'array', 'items': self.element_serializer._schema_fragment(root)}
