from unittest import TestCase
from foundation_kaia.marshalling_2.reflector.declared_type import *
from foundation_kaia.marshalling_2.reflector.annotation import Annotation
from foundation_kaia.tests.test_marshalling_2.test_reflector.test_declared_type.setup import T, Passthrough, Switching

class GenericSwitchingTestCase(TestCase):
    def test_with_type(self):
        result = DeclaredType.parse(Switching)
        self.assertEqual(DeclaredTypeArgumentKind.type, result.kind)
        self.assertEqual(
            result.mro[0],
            DeclaredTypeMROElement(
                Switching,
                Switching[object],
                (
                    GenericParameterDescription(T, Annotation.parse(object)),
                ),
            )
        )
        self.assertEqual(
            DeclaredType.parse(Passthrough[list[object]]).mro,
            result.mro[1:]
        )

    def test_with_generic(self):
        result = DeclaredType.parse(Switching[int])
        self.assertEqual(DeclaredTypeArgumentKind.generic_type, result.kind)
        self.assertEqual(
            result.mro[0],
            DeclaredTypeMROElement(
                Switching,
                Switching[int],
                (
                    GenericParameterDescription(T, Annotation.parse(int)),
                ),
            )
        )
        self.assertEqual(
            DeclaredType.parse(Passthrough[list[int]]).mro,
            result.mro[1:]
        )

    def test_with_value(self):
        v = Switching()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Switching).mro,
            result.mro
        )

    def test_with_generic_value(self):
        v = Switching[int]()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Switching[int]).mro,
            result.mro
        )
