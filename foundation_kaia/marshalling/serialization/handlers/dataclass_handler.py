from __future__ import annotations
from .complex_handler import ComplexHandler
from dataclasses import fields, is_dataclass
from typing import Any, TypeVar, get_type_hints, get_args, TYPE_CHECKING

if TYPE_CHECKING:
    from ..serializer import Serializer
from ...reflector.annotation import Annotation


class DataclassHandler(ComplexHandler):
    type_token = 'dataclass'

    @classmethod
    def is_eligible(cls, value: Any) -> bool:
        return is_dataclass(value)

    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if is_dataclass(annotation):
            return DataclassHandler(annotation, type_map=type_map)
        if origin is not None and is_dataclass(origin):
            type_args = get_args(annotation)
            new_type_map = {**type_map, **dict(zip(origin.__parameters__, type_args))} if type_map else dict(
                zip(origin.__parameters__, type_args))
            return DataclassHandler(origin, type_map=new_type_map)
        return None

    def __init__(self, tp: type | None, type_map: dict[TypeVar, type] | None = None):
        if tp is not None and not is_dataclass(tp):
            raise TypeError(f"{tp} is not a dataclass")
        self.tp = tp
        self._type_map = type_map
        self._fields: dict[str, 'Serializer'] | None = None

    @property
    def fields(self) -> dict[str, 'Serializer']:
        if self._fields is None:
            self._fields = self._parse_fields(self.tp, self._type_map) if self.tp is not None else {}
        return self._fields

    @staticmethod
    def _parse_fields(tp: type, type_map: dict[TypeVar, type] | None = None) -> dict[str, 'Serializer']:
        from ..serializer import Serializer

        hints = get_type_hints(tp)
        result = {}
        for field in fields(tp):
            result[field.name] = Serializer(Annotation.parse(hints[field.name], type_map))
        return result
