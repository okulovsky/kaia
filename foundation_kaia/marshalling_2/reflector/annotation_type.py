from typing import get_origin, Any
from dataclasses import dataclass
from .type_handlers import *
from ..declared_type import DeclaredType


@dataclass
class AnnotationType:
    raw_annotation: Any
    handler: ITypeHandler
    declared_type: DeclaredType|None

    @staticmethod
    def parse(annotation: Any, type_map):
        origin = get_origin(annotation)

        # bool before int — bool is a subclass of int
        parsers = [
            ListHandler, DictHandler,
            NoneHandler, BoolHandler, IntHandler, FloatHandler, StringHandler,
            DateTimeHandler, EnumHandler, PathHandler,
            DataclassHandler,
            UnsupportedHandler,
        ]

        handler = None
        for parser_cls in parsers:
            result = parser_cls.parse(annotation, origin, type_map)
            if result is not None:
                handler = result
                break

        if handler is None:
            raise ValueError(f"Cannot find a handler for annotation {annotation}")

        declared_type = None
        try:
            declared_type = DeclaredType.parse(annotation, type_map)
        except Exception as e:
            pass

        return AnnotationType(annotation, handler, declared_type)