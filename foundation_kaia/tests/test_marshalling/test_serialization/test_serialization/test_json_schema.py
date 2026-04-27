import unittest
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from foundation_kaia.marshalling.serialization import Serializer


class Color(Enum):
    RED = 'red'
    BLUE = 'blue'


@dataclass
class Inner:
    x: int
    flag: bool


@dataclass
class Outer:
    name: str
    value: Optional[int]
    items: list[Inner]
    color: Color



class TestPrimitiveSchemas(unittest.TestCase):

    def test_int(self):
        s = Serializer.parse(int).to_json_schema()
        self.assertEqual({'type': 'integer'}, s.to_dict())

    def test_float(self):
        s = Serializer.parse(float).to_json_schema()
        self.assertEqual({'type': 'number'}, s.to_dict())

    def test_str(self):
        s = Serializer.parse(str).to_json_schema()
        self.assertEqual({'type': 'string'}, s.to_dict())

    def test_bool(self):
        s = Serializer.parse(bool).to_json_schema()
        self.assertEqual({'type': 'boolean'}, s.to_dict())

    def test_none(self):
        s = Serializer.parse(type(None)).to_json_schema()
        self.assertEqual({'type': 'null'}, s.to_dict())

    def test_datetime(self):
        s = Serializer.parse(datetime).to_json_schema()
        self.assertEqual({'type': 'string', 'format': 'date-time'}, s.to_dict())

    def test_path(self):
        s = Serializer.parse(Path).to_json_schema()
        self.assertEqual({'type': 'string', 'format': 'path'}, s.to_dict())

    def test_bytes(self):
        s = Serializer.parse(bytes).to_json_schema()
        d = s.to_dict()
        self.assertEqual('object', d['type'])
        self.assertIn('@type', d['properties'])
        self.assertIn('value', d['properties'])

    def test_enum(self):
        s = Serializer.parse(Color).to_json_schema()
        d = s.to_dict()
        self.assertEqual(['red', 'blue'], d['enum'])


class TestUnionSchema(unittest.TestCase):

    def test_optional_int(self):
        s = Serializer.parse(Optional[int]).to_json_schema()
        d = s.to_dict()
        self.assertIn('anyOf', d)
        types = [alt['type'] for alt in d['anyOf']]
        self.assertIn('integer', types)
        self.assertIn('null', types)

    def test_int_or_str(self):
        s = Serializer.parse(int | str).to_json_schema()
        d = s.to_dict()
        self.assertIn('anyOf', d)
        self.assertEqual(2, len(d['anyOf']))


class TestContainerSchemas(unittest.TestCase):

    def test_list_of_int(self):
        s = Serializer.parse(list[int]).to_json_schema()
        d = s.to_dict()
        self.assertEqual('array', d['type'])
        self.assertEqual({'type': 'integer'}, d['items'])

    def test_dict_str_to_int(self):
        s = Serializer.parse(dict[str, int]).to_json_schema()
        d = s.to_dict()
        self.assertEqual('object', d['type'])
        self.assertEqual({'type': 'integer'}, d['additionalProperties'])


class TestDataclassSchema(unittest.TestCase):

    def test_simple_dataclass(self):
        s = Serializer.parse(Inner).to_json_schema()
        d = s.to_dict()
        self.assertIn('$ref', d)
        self.assertIn('$defs', d)
        ref_name = d['$ref'].split('/')[-1]
        props = d['$defs'][ref_name]['properties']
        self.assertEqual({'type': 'integer'}, props['x'])
        self.assertEqual({'type': 'boolean'}, props['flag'])

    def test_nested_dataclass(self):
        s = Serializer.parse(Outer).to_json_schema()
        d = s.to_dict()
        self.assertIn('$defs', d)
        # Both Outer and Inner should be in $defs
        def_names = list(d['$defs'].keys())
        self.assertTrue(any('Outer' in n for n in def_names))
        self.assertTrue(any('Inner' in n for n in def_names))

    def test_optional_field(self):
        s = Serializer.parse(Outer).to_json_schema()
        d = s.to_dict()
        ref_name = d['$ref'].split('/')[-1]
        value_schema = d['$defs'][ref_name]['properties']['value']
        self.assertIn('anyOf', value_schema)

    def test_list_field_refs_inner(self):
        s = Serializer.parse(Outer).to_json_schema()
        d = s.to_dict()
        ref_name = d['$ref'].split('/')[-1]
        items_schema = d['$defs'][ref_name]['properties']['items']
        self.assertEqual('array', items_schema['type'])
        self.assertIn('$ref', items_schema['items'])


if __name__ == '__main__':
    unittest.main()
