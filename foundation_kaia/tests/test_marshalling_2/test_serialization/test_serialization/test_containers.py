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
class WithContainers:
    names: list[str]
    scores: dict[str, int]
    coords: tuple[float, ...]


class TestContainers(unittest.TestCase):

    def setUp(self):
        self.desc = DataclassHandler(WithContainers)

    def test_round_trip(self):
        obj = WithContainers(
            names=['alice', 'bob'],
            scores={'math': 95, 'english': 88},
            coords=(1.0, 2.0, 3.0),
        )
        json_data = self.desc.to_json(obj, _ctx())
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

    def test_empty_containers(self):
        obj = WithContainers(names=[], scores={}, coords=())
        json_data = self.desc.to_json(obj, _ctx())
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

    def test_json_structure(self):
        obj = WithContainers(
            names=['x'],
            scores={'a': 1, 'b': 2},
            coords=(10.0,),
        )
        json_data = self.desc.to_json(obj, _ctx())
        self.assertEqual(json_data['names'], ['x'])
        # dict serializes as JSON object with string keys
        self.assertIsInstance(json_data['scores'], dict)
        self.assertEqual(json_data['scores']['a'], 1)
        self.assertEqual(json_data['scores']['b'], 2)
        # tuple serializes as list
        self.assertEqual(json_data['coords'], [10.0])

