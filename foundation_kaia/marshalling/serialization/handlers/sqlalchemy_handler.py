from __future__ import annotations
from .complex_handler import ComplexHandler
from typing import Any, TypeVar, get_type_hints, get_args, TYPE_CHECKING

if TYPE_CHECKING:
    from ..serializer import Serializer
from ...reflector.annotation import Annotation


def _is_sqlalchemy_model(tp) -> bool:
    return isinstance(tp, type) and hasattr(tp, '__mapper__') and hasattr(tp, '__tablename__')


class SqlalchemyHandler(ComplexHandler):
    type_token = 'sqlalchemy'

    @classmethod
    def is_eligible(cls, value: Any) -> bool:
        return _is_sqlalchemy_model(type(value))

    @staticmethod
    def parse(annotation, origin, type_map: dict[TypeVar, type] | None = None):
        if _is_sqlalchemy_model(annotation):
            return SqlalchemyHandler(annotation)
        return None

    def __init__(self, tp: type | None):
        self.tp = tp
        self.fields: dict[str, 'Serializer'] = self._parse_fields(tp) if tp is not None else {}

    @staticmethod
    def _parse_fields(tp: type) -> dict[str, 'Serializer']:
        from ..serializer import Serializer

        column_names = {attr.key for attr in tp.__mapper__.column_attrs}
        hints = get_type_hints(tp)
        result = {}
        for name, hint in hints.items():
            if name not in column_names:
                continue
            args = get_args(hint)
            inner = args[0] if args else hint
            result[name] = Serializer(Annotation.parse(inner))
        return result
