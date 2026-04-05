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
class Point:
    x: float
    y: float

class TestErrorPaths(unittest.TestCase):

    def test_wrong_type_error_has_path(self):
        desc = DataclassHandler(Point)
        with self.assertRaises((TypeError, ValueError)) as cm:
            desc.from_json({'x': 'not_a_number', 'y': 1.0}, _ctx())
        self.assertIn('x', str(cm.exception))

    def test_missing_field_error(self):
        desc = DataclassHandler(Point)
        with self.assertRaises((TypeError, ValueError, KeyError)):
            desc.from_json({'x': 1.0}, _ctx())

