import unittest
from avatar.messaging.rules.rule_creator import get_annotated_output_type
from avatar.daemon.common.known_messages import TextCommand
from typing import *

class TestGetAnnotatedOutputType(unittest.TestCase):
    def test_no_annotation(self):
        def handler():
            pass
        self.assertIsNone(get_annotated_output_type(handler))

    def test_simple_annotation(self):
        def handler() -> int:
            pass
        self.assertEqual((int,), get_annotated_output_type(handler))

    def test_union_annotation(self):
        def handler() -> Union[int, str]:
            pass
        self.assertEqual(
            {int, str},
            set(get_annotated_output_type(handler)),
        )

    def test_union_annotation_2(self):
        def handler() -> int|str:
            pass
        self.assertEqual(
            {int, str},
            set(get_annotated_output_type(handler)),
        )


    def test_tuple_annotation(self):
        def handler() -> Tuple[int, str]:
            pass
        self.assertEqual(
            {int, str},
            set(get_annotated_output_type(handler)),
        )

    def test_tuple_annotation_2(self):
        def handler() -> tuple[int, str]:
            pass
        self.assertEqual(
            {int, str},
            set(get_annotated_output_type(handler)),
        )

    def test_tuple_annotation_3(self):
        def handler() -> tuple[int|str,...]:
            pass
        self.assertEqual(
            {int, str},
            set(get_annotated_output_type(handler)),
        )

    def test_nested_tuple_and_union_annotation(self):
        def handler() -> Tuple[Union[int, str], Tuple[bool, bytes]]:
            pass
        self.assertEqual(
            {int, str, bool, bytes},
            set(get_annotated_output_type(handler)),
        )


    def test_none(self):
        def handler() -> None:
            pass
        self.assertIsNone(get_annotated_output_type(handler))