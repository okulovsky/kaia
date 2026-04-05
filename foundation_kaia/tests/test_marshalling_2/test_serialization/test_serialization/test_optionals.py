import unittest
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, Any

from foundation_kaia.marshalling_2.serialization.handlers.type_handler import SerializationContext
from foundation_kaia.marshalling_2.serialization.handlers.dataclass_handler import DataclassHandler

def _ctx():
    return SerializationContext(path=[], allow_base64=True)


@dataclass
class WithOptionals:
    name: str
    tag: int | None
    label: str | None




class TestOptionals(unittest.TestCase):

    def setUp(self):
        self.desc = DataclassHandler(WithOptionals)

    def test_all_present(self):
        obj = WithOptionals(name='test', tag=5, label='foo')
        json_data = self.desc.to_json(obj, _ctx())
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

    def test_nulls(self):
        obj = WithOptionals(name='test', tag=None, label=None)
        json_data = self.desc.to_json(obj, _ctx())
        self.assertIsNone(json_data['tag'])
        self.assertIsNone(json_data['label'])
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

    def test_mixed(self):
        obj = WithOptionals(name='a', tag=10, label=None)
        json_data = self.desc.to_json(obj, _ctx())
        self.assertEqual(json_data['tag'], 10)
        self.assertIsNone(json_data['label'])
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)
