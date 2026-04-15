from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class JsonSchema:
    schema: dict = field(default_factory=dict)
    defs: dict[str, dict] = field(default_factory=dict)

    @staticmethod
    def from_fields(fields: dict[str, 'JsonSchema']) -> 'JsonSchema':
        result = JsonSchema()
        properties = {}
        for name, field_schema in fields.items():
            result.defs.update(field_schema.defs)
            properties[name] = field_schema.schema
        result.schema = {'type': 'object', 'properties': properties}
        return result

    def to_dict(self) -> dict:
        result = dict(self.schema)
        if self.defs:
            result['$defs'] = self.defs
        return result
