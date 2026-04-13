import unittest
from typing import Optional
from enum import Enum
from dataclasses import dataclass

from foundation_kaia.marshalling.serialization import (
    Serializer, IntHandler, FloatHandler, StringHandler, DataclassHandler,
    NoneHandler, ListHandler, DictHandler,
)


class Color(Enum):
    RED = 'red'
    GREEN = 'green'


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Label:
    name: str
    value: int


class TestParseDataclass(unittest.TestCase):

    def test_simple_dataclass(self):
        result = Serializer.parse(Point)
        self.assertEqual(len(result.handlers), 1)
        desc = result.handlers[0]
        self.assertIsInstance(desc, DataclassHandler)
        self.assertIs(desc.python_type, Point)
        self.assertIn('x', desc.fields)
        self.assertIn('y', desc.fields)
        self.assertIsInstance(desc.fields['x'].handlers[0], FloatHandler)
        self.assertIsInstance(desc.fields['y'].handlers[0], FloatHandler)

    def test_dataclass_with_various_fields(self):
        result = Serializer.parse(Label)
        desc = result.handlers[0]
        self.assertIsInstance(desc, DataclassHandler)
        self.assertIsInstance(desc.fields['name'].handlers[0], StringHandler)
        self.assertIsInstance(desc.fields['value'].handlers[0], IntHandler)

    def test_nested_dataclass(self):
        @dataclass
        class Shape:
            origin: Point
            name: str

        result = Serializer.parse(Shape)
        desc = result.handlers[0]
        self.assertIsInstance(desc, DataclassHandler)
        self.assertIsInstance(desc.fields['origin'].handlers[0], DataclassHandler)
        self.assertIs(desc.fields['origin'].handlers[0].python_type, Point)
        self.assertIsInstance(desc.fields['name'].handlers[0], StringHandler)

    def test_dataclass_with_optional_field(self):
        @dataclass
        class Item:
            name: str
            tag: int | None

        result = Serializer.parse(Item)
        desc = result.handlers[0]
        tag_serializer = desc.fields['tag']
        self.assertEqual(len(tag_serializer.handlers), 2)
        types = {type(h) for h in tag_serializer.handlers}
        self.assertEqual(types, {IntHandler, NoneHandler})

    def test_dataclass_with_list_field(self):
        @dataclass
        class Container:
            items: list[int]

        result = Serializer.parse(Container)
        desc = result.handlers[0]
        self.assertIsInstance(desc.fields['items'].handlers[0], ListHandler)

    def test_dataclass_with_dict_field(self):
        @dataclass
        class Config:
            settings: dict[str, int]

        result = Serializer.parse(Config)
        desc = result.handlers[0]
        self.assertIsInstance(desc.fields['settings'].handlers[0], DictHandler)

    def test_optional_dataclass(self):
        result = Serializer.parse(Optional[Point])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {DataclassHandler, NoneHandler})

    def test_list_of_dataclasses(self):
        result = Serializer.parse(list[Point])
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertIsInstance(desc.element_serializer.handlers[0], DataclassHandler)
