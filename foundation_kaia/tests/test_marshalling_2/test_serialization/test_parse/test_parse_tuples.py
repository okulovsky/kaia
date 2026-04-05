import unittest

from foundation_kaia.marshalling_2.serialization import (
    Serializer, IntHandler, FloatHandler, StringHandler, ListHandler,
)


class TestParseTuple(unittest.TestCase):

    def test_tuple_homogeneous(self):
        result = Serializer.parse(tuple[int, ...])
        self.assertEqual(len(result.handlers), 1)
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertIs(desc.python_type, tuple)
        self.assertTrue(desc.as_tuple)
        self.assertEqual(len(desc.element_serializer.handlers), 1)
        self.assertIsInstance(desc.element_serializer.handlers[0], IntHandler)

    def test_tuple_heterogeneous(self):
        result = Serializer.parse(tuple[int, str])
        self.assertEqual(len(result.handlers), 1)
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertTrue(desc.as_tuple)
        self.assertEqual(len(desc.element_serializer.handlers), 2)
        self.assertIsInstance(desc.element_serializer.handlers[0], IntHandler)
        self.assertIsInstance(desc.element_serializer.handlers[1], StringHandler)

    def test_tuple_heterogeneous_three(self):
        result = Serializer.parse(tuple[int, str, float])
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertTrue(desc.as_tuple)
        self.assertEqual(len(desc.element_serializer.handlers), 3)
        self.assertIsInstance(desc.element_serializer.handlers[0], IntHandler)
        self.assertIsInstance(desc.element_serializer.handlers[1], StringHandler)
        self.assertIsInstance(desc.element_serializer.handlers[2], FloatHandler)
