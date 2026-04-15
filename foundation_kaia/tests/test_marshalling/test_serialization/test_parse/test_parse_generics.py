import unittest
from typing import Generic, TypeVar
from dataclasses import dataclass

from foundation_kaia.marshalling.serialization import (
    Serializer, IntHandler, FloatHandler, StringHandler,
    ListHandler, DataclassHandler, UnannotatedHandler,
)

T = TypeVar('T')
U = TypeVar('U')


class TestParseTypeVar(unittest.TestCase):

    def test_typevar_without_map_returns_unannotated(self):
        result = Serializer.parse(T)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], UnannotatedHandler)

    def test_typevar_with_map_resolves_to_int(self):
        result = Serializer.parse(T, type_map={T: int})
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], IntHandler)

    def test_typevar_with_map_resolves_to_str(self):
        result = Serializer.parse(T, type_map={T: str})
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], StringHandler)

    def test_typevar_not_in_map_returns_unannotated(self):
        result = Serializer.parse(U, type_map={T: int})
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], UnannotatedHandler)

    def test_list_of_typevar(self):
        result = Serializer.parse(list[T], type_map={T: int})
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], ListHandler)
        self.assertIsInstance(result.handlers[0].element_serializer.handlers[0], IntHandler)

    def test_typevar_resolves_to_dataclass(self):
        @dataclass
        class Point:
            x: float
            y: float

        result = Serializer.parse(T, type_map={T: Point})
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], DataclassHandler)
        self.assertIs(result.handlers[0].python_type, Point)


class TestParseGenericDataclass(unittest.TestCase):

    def test_generic_dataclass_with_int(self):
        @dataclass
        class Box(Generic[T]):
            value: T

        result = Serializer.parse(Box[int])
        self.assertEqual(len(result.handlers), 1)
        desc = result.handlers[0]
        self.assertIsInstance(desc, DataclassHandler)
        self.assertIs(desc.python_type, Box)
        self.assertIsInstance(desc.fields['value'].handlers[0], IntHandler)

    def test_generic_dataclass_with_str(self):
        @dataclass
        class Box(Generic[T]):
            value: T

        result = Serializer.parse(Box[str])
        desc = result.handlers[0]
        self.assertIsInstance(desc.fields['value'].handlers[0], StringHandler)

    def test_generic_dataclass_two_params(self):
        @dataclass
        class Pair(Generic[T, U]):
            first: T
            second: U

        result = Serializer.parse(Pair[int, str])
        desc = result.handlers[0]
        self.assertIsInstance(desc, DataclassHandler)
        self.assertIsInstance(desc.fields['first'].handlers[0], IntHandler)
        self.assertIsInstance(desc.fields['second'].handlers[0], StringHandler)

    def test_generic_dataclass_with_concrete_and_generic_fields(self):
        @dataclass
        class Tagged(Generic[T]):
            value: T
            name: str

        result = Serializer.parse(Tagged[float])
        desc = result.handlers[0]
        self.assertIsInstance(desc.fields['value'].handlers[0], FloatHandler)
        self.assertIsInstance(desc.fields['name'].handlers[0], StringHandler)

    def test_generic_dataclass_with_list_of_typevar(self):
        @dataclass
        class Collection(Generic[T]):
            items: list[T]

        result = Serializer.parse(Collection[int])
        desc = result.handlers[0]
        items_handler = desc.fields['items'].handlers[0]
        self.assertIsInstance(items_handler, ListHandler)
        self.assertIsInstance(items_handler.element_serializer.handlers[0], IntHandler)


if __name__ == '__main__':
    unittest.main()
