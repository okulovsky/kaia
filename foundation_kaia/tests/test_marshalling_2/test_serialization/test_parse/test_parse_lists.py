import unittest
from typing import Optional
from dataclasses import dataclass

from foundation_kaia.marshalling_2.serialization import (
    Serializer, IntHandler, StringHandler, DataclassHandler, NoneHandler, ListHandler,
)


@dataclass
class Point:
    x: float
    y: float


class TestParseList(unittest.TestCase):

    def test_list_int(self):
        result = Serializer.parse(list[int])
        self.assertEqual(len(result.handlers), 1)
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertIs(desc.python_type, list)
        self.assertEqual(len(desc.element_serializer.handlers), 1)
        self.assertIsInstance(desc.element_serializer.handlers[0], IntHandler)

    def test_list_str(self):
        result = Serializer.parse(list[str])
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertIsInstance(desc.element_serializer.handlers[0], StringHandler)

    def test_list_str_or_int(self):
        result = Serializer.parse(list[str | int])
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertEqual(2, len(desc.element_serializer.handlers))
        self.assertIsInstance(desc.element_serializer.handlers[0], StringHandler)
        self.assertIsInstance(desc.element_serializer.handlers[1], IntHandler)

    def test_list_of_dataclass(self):
        result = Serializer.parse(list[Point])
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertEqual(len(desc.element_serializer.handlers), 1)
        self.assertIsInstance(desc.element_serializer.handlers[0], DataclassHandler)
        self.assertIs(desc.element_serializer.handlers[0].python_type, Point)

    def test_list_of_optional(self):
        result = Serializer.parse(list[int | None])
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertEqual(len(desc.element_serializer.handlers), 2)
        types = {type(h) for h in desc.element_serializer.handlers}
        self.assertEqual(types, {IntHandler, NoneHandler})

    def test_optional_list(self):
        result = Serializer.parse(Optional[list[int]])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertIn(NoneHandler, types)
        self.assertIn(ListHandler, types)
