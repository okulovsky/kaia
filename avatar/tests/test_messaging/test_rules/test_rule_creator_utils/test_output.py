import unittest
from foundation_kaia.marshalling.reflector.signature import Signature
from avatar.messaging.rules.rule_creator import _get_output_types
from typing import Union, Tuple


def _output_types(func):
    return _get_output_types(Signature.parse(func))


class TestGetAnnotatedOutputType(unittest.TestCase):

    def test_tuple_annotation(self):
        def handler() -> Tuple[int, str]:
            pass
        self.assertEqual({int, str}, set(_output_types(handler)))

    def test_tuple_annotation_2(self):
        def handler() -> tuple[int, str]:
            pass
        self.assertEqual({int, str}, set(_output_types(handler)))

    def test_tuple_annotation_3(self):
        def handler() -> tuple[int | str, ...]:
            pass
        self.assertEqual({int, str}, set(_output_types(handler)))

    def test_nested_tuple_and_union_annotation(self):
        def handler() -> Tuple[Union[int, str], Tuple[bool, bytes]]:
            pass
        self.assertEqual({int, str, bool, bytes}, set(_output_types(handler)))

    def test_none(self):
        def handler() -> None:
            pass
        self.assertIsNone(_output_types(handler))
