import unittest
from dataclasses import dataclass
from typing import Optional

from foundation_kaia.marshalling_2.serialization import Serializer
from foundation_kaia.marshalling_2.serialization.json_schema import JsonSchema


@dataclass
class Point:
    x: int
    y: int


class TestFromFields(unittest.TestCase):

    def test_primitive_fields(self):
        result = JsonSchema.from_fields({
            'name': Serializer.parse(str).to_json_schema(),
            'count': Serializer.parse(int).to_json_schema(),
        })
        d = result.to_dict()
        self.assertEqual('object', d['type'])
        self.assertEqual({'type': 'string'}, d['properties']['name'])
        self.assertEqual({'type': 'integer'}, d['properties']['count'])

    def test_empty_fields(self):
        result = JsonSchema.from_fields({})
        d = result.to_dict()
        self.assertEqual('object', d['type'])
        self.assertEqual({}, d['properties'])
        self.assertNotIn('$defs', d)

    def test_dataclass_field_populates_defs(self):
        result = JsonSchema.from_fields({
            'point': Serializer.parse(Point).to_json_schema(),
        })
        d = result.to_dict()
        self.assertIn('$defs', d)
        self.assertTrue(any('Point' in k for k in d['$defs']))
        self.assertIn('$ref', d['properties']['point'])

    def test_defs_merged_across_fields(self):
        result = JsonSchema.from_fields({
            'a': Serializer.parse(Point).to_json_schema(),
            'b': Serializer.parse(Point).to_json_schema(),
        })
        d = result.to_dict()
        # Point should appear only once in $defs even though used twice
        point_defs = [k for k in d['$defs'] if 'Point' in k]
        self.assertEqual(1, len(point_defs))

    def test_optional_field(self):
        result = JsonSchema.from_fields({
            'value': Serializer.parse(Optional[int]).to_json_schema(),
        })
        d = result.to_dict()
        self.assertIn('anyOf', d['properties']['value'])

    def test_field_order_preserved(self):
        result = JsonSchema.from_fields({
            'z': Serializer.parse(str).to_json_schema(),
            'a': Serializer.parse(int).to_json_schema(),
            'm': Serializer.parse(float).to_json_schema(),
        })
        self.assertEqual(['z', 'a', 'm'], list(result.schema['properties'].keys()))


if __name__ == '__main__':
    unittest.main()
