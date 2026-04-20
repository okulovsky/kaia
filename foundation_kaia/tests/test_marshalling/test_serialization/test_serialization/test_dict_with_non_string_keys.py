import unittest
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, Any

from foundation_kaia.marshalling.serialization.handlers.type_handler import SerializationContext
from foundation_kaia.marshalling.serialization.handlers.dataclass_handler import DataclassHandler

def _ctx():
    return SerializationContext(path=[], allow_base64=True)


class Color(Enum):
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'


class TestDictWithNonStringKeys(unittest.TestCase):

    def test_int_keys(self):
        @dataclass
        class IntKeyed:
            mapping: dict[int, str]

        desc = DataclassHandler(IntKeyed)
        obj = IntKeyed(mapping={1: 'one', 2: 'two'})
        json_data = desc.to_json(obj, _ctx())
        # int keys become string keys in JSON
        self.assertIn('1', json_data['mapping'])
        self.assertIn('2', json_data['mapping'])
        restored = desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

    def test_enum_keys(self):
        @dataclass
        class EnumKeyed:
            mapping: dict[Color, int]

        desc = DataclassHandler(EnumKeyed)
        obj = EnumKeyed(mapping={Color.RED: 1, Color.BLUE: 3})
        json_data = desc.to_json(obj, _ctx())
        self.assertIn('RED', json_data['mapping'])
        self.assertIn('BLUE', json_data['mapping'])
        restored = desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

