from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, ClassVar, TYPE_CHECKING

from .type_handler import ITypeHandler, SerializationContext
from ..json_schema import JsonSchema
from ..tools import TypeTools

if TYPE_CHECKING:
    from ..serializer import Serializer


class ComplexHandler(ITypeHandler):
    type_token: ClassVar[str]

    # Subclasses must set self.tp: type | None and self.fields: dict[str, Serializer]

    @classmethod
    @abstractmethod
    def is_eligible(cls, value: Any) -> bool: ...

    @property
    def python_type(self) -> type:
        return self.tp if self.tp is not None else object

    def to_json(self, value: Any, context: SerializationContext) -> Any:
        if self.tp is None or type(value) is not self.tp:
            from ..tools import TypeTools
            actual = type(self)(type(value))
            result = actual._to_json_fields(value, context)
            result['@type'] = self.type_token
            result['@subtype'] = TypeTools.type_to_full_name(type(value))
            return result
        return self._to_json_fields(value, context)

    def _to_json_fields(self, value: Any, context: SerializationContext) -> dict:
        result = {}
        for field_name, field_serializer in self.fields.items():
            with context.subpath(field_name):
                result[field_name] = field_serializer.to_json(getattr(value, field_name), context)
        return result

    def from_json(self, json_value: Any, context: SerializationContext) -> Any:
        if not isinstance(json_value, dict):
            raise TypeError(f"Expected dict at {context.current_path}, got {type(json_value)}")
        type_tag = json_value.get('@type')
        if type_tag == self.type_token:
            from ..tools import TypeTools
            tp = TypeTools.full_name_to_type(json_value['@subtype'])
            actual = type(self)(tp)
            json_copy = {k: v for k, v in json_value.items() if k not in ('@type', '@subtype')}
            return actual._from_json_fields(json_copy, context)
        if type_tag is not None:
            raise TypeError(
                f"Expected @type='{self.type_token}' at {context.current_path}, got '{type_tag}'"
            )
        if self.tp is None:
            raise TypeError(f"Cannot deserialize without @type='{self.type_token}' marker at {context.current_path}")
        return self._from_json_fields(json_value, context)

    def _from_json_fields(self, json_value: dict, context: SerializationContext) -> Any:
        kwargs = {}
        for field_name, field_value in json_value.items():
            if field_name not in self.fields:
                raise ValueError(f"Unexpected field '{field_name}' at {context.current_path}")
            with context.subpath(field_name):
                kwargs[field_name] = self.fields[field_name].from_json(field_value, context)
        return self.tp(**kwargs)

    def to_json_schema(self, root: JsonSchema) -> dict:
        if self.tp is None:
            return {}
        ref_name = TypeTools.type_to_full_name(self.tp)
        if ref_name not in root.defs:
            # Insert a placeholder first to handle recursive types
            root.defs[ref_name] = {}
            root.defs[ref_name] = {
                'type': 'object',
                'properties': {name: ser._schema_fragment(root) for name, ser in self.fields.items()},
            }
        return {'$ref': f'#/$defs/{ref_name}'}
