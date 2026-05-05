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


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# --- Test models ---

@dataclass
class AllPrimitives:
    i: int
    f: float
    s: str
    b: bool
    color: Color
    priority: Priority
    when: datetime



class TestAllPrimitives(unittest.TestCase):

    def setUp(self):
        self.desc = DataclassHandler(AllPrimitives)
        self.obj = AllPrimitives(
            i=42,
            f=3.14,
            s='hello',
            b=True,
            color=Color.GREEN,
            priority=Priority.HIGH,
            when=datetime(2025, 6, 15, 10, 30, 0),
        )

    def test_round_trip(self):
        ctx = _ctx()
        json_data = self.desc.to_json(self.obj, ctx)
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(self.obj, restored)

    def test_json_structure(self):
        json_data = self.desc.to_json(self.obj, _ctx())
        self.assertEqual(json_data['i'], 42)
        self.assertAlmostEqual(json_data['f'], 3.14)
        self.assertEqual(json_data['s'], 'hello')
        self.assertIs(json_data['b'], True)
        self.assertEqual(json_data['color'], 'GREEN')
        self.assertEqual(json_data['priority'], 'HIGH')
        self.assertEqual(json_data['when'], '2025-06-15T10:30:00')

    def test_int_to_float_coercion(self):
        """An int value in a float field should serialize fine."""
        obj = AllPrimitives(i=1, f=7, s='x', b=False, color=Color.RED,
                            priority=Priority.LOW, when=datetime(2025, 1, 1))
        json_data = self.desc.to_json(obj, _ctx())
        self.assertIsInstance(json_data['f'], float)
        self.assertEqual(json_data['f'], 7.0)
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(restored.f, 7.0)
