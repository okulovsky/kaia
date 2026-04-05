from collections.abc import Iterable
from dataclasses import dataclass
from unittest import TestCase
from foundation_kaia.marshalling_2.reflector.declared_type import DeclaredType, DeclaredTypeArgumentKind
from foundation_kaia.marshalling_2.reflector.annotation import Annotation


@dataclass
class Item:
    name: str
    value: int


class IterableTypeDescriptionTestCase(TestCase):
    def test_iterable_bytes(self):
        desc = DeclaredType.parse(Iterable[bytes])
        self.assertEqual(desc.kind, DeclaredTypeArgumentKind.generic_type)
        entry = desc.mro[0]
        self.assertIs(entry.type, Iterable)
        self.assertEqual(len(entry.parameters), 1)
        self.assertEqual(entry.parameters[0].generic_parameter_value, Annotation.parse(bytes))

    def test_iterable_str(self):
        desc = DeclaredType.parse(Iterable[str])
        entry = desc.mro[0]
        self.assertIs(entry.type, Iterable)
        self.assertEqual(len(entry.parameters), 1)
        self.assertEqual(entry.parameters[0].generic_parameter_value, Annotation.parse(str))

    def test_iterable_int(self):
        desc = DeclaredType.parse(Iterable[int])
        entry = desc.mro[0]
        self.assertIs(entry.type, Iterable)
        self.assertEqual(entry.parameters[0].generic_parameter_value, Annotation.parse(int))

    def test_iterable_dataclass(self):
        desc = DeclaredType.parse(Iterable[Item])
        entry = desc.mro[0]
        self.assertIs(entry.type, Iterable)
        self.assertEqual(entry.parameters[0].generic_parameter_value, Annotation.parse(Item))
