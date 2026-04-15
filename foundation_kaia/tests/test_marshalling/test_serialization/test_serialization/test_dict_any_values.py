import unittest
from dataclasses import dataclass
from typing import Any, Dict

from foundation_kaia.marshalling.serialization.handlers.type_handler import SerializationContext
from foundation_kaia.marshalling.serialization.handlers.dataclass_handler import DataclassHandler


def _ctx():
    return SerializationContext(path=[], allow_base64=True)


@dataclass
class Point:
    x: float
    y: float


class Opaque:
    def __init__(self, v):
        self.v = v
    def __eq__(self, other):
        return isinstance(other, Opaque) and self.v == other.v


@dataclass
class WithDictAny:
    data: Dict[str, Any]


class TestDictAnyValues(unittest.TestCase):
    """
    Documents how dict[str, Any] values are encoded depending on the value type.

    - Primitives (int, str, float, bool, None): serialized as-is — no wrapping
    - Lists: serialized as JSON arrays, elements handled recursively as Any
    - Dicts: serialized as JSON objects, values handled recursively as Any
    - Dataclasses: serialized inline with '@type': 'dataclass' and '@subtype'
      containing the fully-qualified class name
    - Completely unknown objects (plain classes): pickle + base64
      encoded as {'@type': '@base64', '@content': '...'}
    """

    def setUp(self):
        self.handler = DataclassHandler(WithDictAny)

    def _roundtrip(self, value):
        obj = WithDictAny(data={"key": value})
        json_data = self.handler.to_json(obj, _ctx())
        print(json_data)
        restored = self.handler.from_json(json_data, _ctx())
        return json_data["data"]["key"], restored.data["key"]

    def test_primitive_int_is_passed_through(self):
        encoded, restored = self._roundtrip(42)
        self.assertEqual(encoded, 42)
        self.assertEqual(restored, 42)

    def test_primitive_str_is_passed_through(self):
        encoded, restored = self._roundtrip("hello")
        self.assertEqual(encoded, "hello")
        self.assertEqual(restored, "hello")

    def test_primitive_none_is_passed_through(self):
        encoded, restored = self._roundtrip(None)
        self.assertIsNone(encoded)
        self.assertIsNone(restored)

    def test_list_is_serialized_as_array(self):
        encoded, restored = self._roundtrip([1, 2, 3])
        self.assertEqual(encoded, [1, 2, 3])
        self.assertEqual(restored, [1, 2, 3])

    def test_list_with_dataclass_elements(self):
        encoded, restored = self._roundtrip([Point(1.0, 2.0)])
        self.assertIsInstance(encoded, list)
        self.assertEqual(encoded[0]['@type'], 'dataclass')
        self.assertIn('Point', encoded[0]['@subtype'])
        self.assertEqual(restored, [Point(1.0, 2.0)])

    def test_dataclass_gets_type_and_subtype(self):
        encoded, restored = self._roundtrip(Point(1.0, 2.0))
        self.assertEqual(encoded['@type'], 'dataclass')
        self.assertIn('Point', encoded['@subtype'])
        self.assertEqual(encoded['x'], 1.0)
        self.assertEqual(encoded['y'], 2.0)
        self.assertEqual(restored, Point(1.0, 2.0))

    def test_unknown_object_is_base64_pickled(self):
        encoded, restored = self._roundtrip(Opaque(99))
        self.assertEqual(encoded['@type'], '@base64')
        self.assertIn('@content', encoded)
        self.assertEqual(restored, Opaque(99))
