import unittest
import types
from foundation_kaia.marshalling_2.reflector.signature import Signature
from avatar.messaging.rules.rule_creator import _get_input_type


def _input_type(func):
    f = func.__func__ if isinstance(func, types.MethodType) else func
    return _get_input_type(Signature.parse(f))


class TestGetSingleArgumentType(unittest.TestCase):

    def test_function_with_multiple_arguments(self):
        def bad_handler(a, b):
            pass
        with self.assertRaises(ValueError):
            _input_type(bad_handler)

    def test_bound_method(self):
        class MyClass:
            def method(self, value: float):
                pass
        self.assertEqual(_input_type(MyClass().method), float)
