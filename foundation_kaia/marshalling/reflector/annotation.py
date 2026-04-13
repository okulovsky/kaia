from __future__ import annotations
from dataclasses import dataclass
from typing import Any, TypeVar, get_origin, get_args, Union, Iterator
from .declared_type import DeclaredType
import types as builtin_types


@dataclass
class Annotation:
    types: tuple[DeclaredType, ...]
    raw_annotation: Any
    not_annotated: bool = False
    from_typevar: TypeVar | None = None

    def __iter__(self) -> Iterator[DeclaredType]:
        return iter(self.types)

    def __len__(self) -> int:
        return len(self.types)

    def __getitem__(self, item) -> DeclaredType:
        return self.types[item]

    @staticmethod
    def parse(annotation: Any, type_map: dict[TypeVar, type] | None = None) -> 'Annotation':
        if isinstance(annotation, TypeVar):
            if type_map and annotation in type_map:
                result = Annotation.parse(type_map[annotation], type_map)
                return Annotation(result.types, result.raw_annotation, result.not_annotated, from_typevar=annotation)
            return Annotation.default()

        origin = get_origin(annotation)

        if origin is Union or isinstance(annotation, builtin_types.UnionType):
            types = []
            for arg in get_args(annotation):
                sub = Annotation.parse(arg, type_map)
                types.extend(sub.types)
            return Annotation(types=tuple(types), raw_annotation=annotation)

        try:
            dt = DeclaredType.parse(annotation, type_map)
            return Annotation(types=(dt,), raw_annotation=annotation)
        except Exception:
            return Annotation.default()

    def is_single_type(self, tp: type) -> bool:
        if len(self.types) != 1:
            return False
        return self.types[0].mro[0].type is tp

    @staticmethod
    def default() -> 'Annotation':
        return Annotation(types=(), raw_annotation=None, not_annotated=True)


