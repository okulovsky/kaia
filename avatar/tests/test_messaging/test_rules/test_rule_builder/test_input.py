import unittest
import inspect
from avatar.messaging.rules.rule_collection import get_single_argument_type

class TestGetSingleArgumentType(unittest.TestCase):

    def test_function_with_one_argument_and_annotation(self):
        def handler(x: int):
            pass
        self.assertEqual(get_single_argument_type(handler), int)

    def test_function_with_one_argument_no_annotation(self):
        def handler(x):
            pass
        self.assertIsNone(get_single_argument_type(handler))

    def test_function_with_multiple_arguments(self):
        def bad_handler(a, b):
            pass
        with self.assertRaises(ValueError):
            get_single_argument_type(bad_handler)

    def test_bound_method(self):
        class MyClass:
            def method(self, value: float):
                pass
        obj = MyClass()
        self.assertEqual(get_single_argument_type(obj.method), float)

    def test_staticmethod(self):
        class MyClass:
            @staticmethod
            def sm(val: list):
                pass
        self.assertEqual(get_single_argument_type(MyClass.sm), list)

    def get_generic_argument(self):
        def handler(x: list[int]):
            pass
        self.assertEqual(list, get_single_argument_type(handler))