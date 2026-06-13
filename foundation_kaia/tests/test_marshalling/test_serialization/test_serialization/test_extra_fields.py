import unittest
from dataclasses import dataclass

from foundation_kaia.marshalling.serialization.handlers.dataclass_handler import DataclassHandler
from foundation_kaia.marshalling.serialization.handlers.type_handler import SerializationContext


def _ctx():
    return SerializationContext(path=[], allow_base64=True)


@dataclass
class Simple:
    x: int
    y: str

    def method(self):
        pass


@dataclass
class Inner:
    v: int


class TestExtraFields(unittest.TestCase):

    def test_extra_field_serialized(self):
        obj = Simple(x=1, y='a')
        obj.extra = 42
        result = DataclassHandler(Simple).to_json(obj, _ctx())
        self.assertEqual(
            {'x': 1, 'y': 'a', 'extra': 42},
            result
        )

    def test_extra_field_round_trip(self):
        obj = Simple(x=1, y='a')
        obj.extra = 42
        handler = DataclassHandler(Simple)
        restored = handler.from_json(handler.to_json(obj, _ctx()), _ctx())
        self.assertEqual(restored.x, 1)
        self.assertEqual(restored.y, 'a')
        self.assertEqual(restored.extra, 42)

    def test_extra_field_complex_value(self):
        obj = Simple(x=0, y='b')
        obj.nested = Inner(v=99)
        handler = DataclassHandler(Simple)
        js = handler.to_json(obj, _ctx())
        print(js)
        restored = handler.from_json(js, _ctx())
        self.assertEqual(restored.nested.v, 99)

    def test_no_extra_fields_unchanged(self):
        obj = Simple(x=3, y='c')
        handler = DataclassHandler(Simple)
        restored = handler.from_json(handler.to_json(obj, _ctx()), _ctx())
        self.assertEqual(restored, obj)
        self.assertEqual(vars(restored), {'x': 3, 'y': 'c'})
