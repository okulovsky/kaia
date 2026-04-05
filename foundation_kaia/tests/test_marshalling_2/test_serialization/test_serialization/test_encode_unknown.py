import unittest
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, Any

from foundation_kaia.marshalling_2.serialization.handlers.type_handler import SerializationContext
from foundation_kaia.marshalling_2.serialization.handlers.dataclass_handler import DataclassHandler

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
class Point:
    x: float
    y: float


class MyClass:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

@dataclass
class TreeNode:
    value: int
    children: list[Any]


class TestEncodeUnknown(unittest.TestCase):

    def test_unknown_dataclass_via_any(self):
        """A dataclass in an Any field gets @type tag."""
        desc = DataclassHandler(TreeNode)
        obj = TreeNode(value=1, children=[Point(1.0, 2.0)])
        json_data = desc.to_json(obj, _ctx())
        child = json_data['children'][0]
        self.assertIn('@type', child)
        self.assertEqual(child['x'], 1.0)
        restored = desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

    def test_tuple_in_any_field_roundtrips_as_list(self):
        """Known inconsistency: a tuple stored in an Any field comes back as a list.
        Tuples and lists are both serialized as JSON arrays; type information is lost."""
        desc = DataclassHandler(TreeNode)
        obj = TreeNode(value=1, children=(10, 20, 30))
        json_data = desc.to_json(obj, _ctx())
        self.assertIsInstance(json_data['children'], list)
        restored = desc.from_json(json_data, _ctx())
        self.assertIsInstance(restored.children, list)       # comes back as list, not tuple
        self.assertEqual(list(obj.children), restored.children)

    def test_pickle_fallback(self):
        """A non-dataclass object in an Any field gets base64 pickled."""
        desc = DataclassHandler(TreeNode)
        obj = TreeNode(value=1, children=[MyClass(3,4)])
        json_data = desc.to_json(obj, _ctx())
        print(json_data)
        child = json_data['children'][0]
        self.assertEqual(child['@type'], '@base64')
        self.assertIn('@content', child)
        restored = desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

