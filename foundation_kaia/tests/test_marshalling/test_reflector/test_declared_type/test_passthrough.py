from unittest import TestCase
from foundation_kaia.marshalling.reflector.declared_type import *
from foundation_kaia.marshalling.reflector.annotation import Annotation
from foundation_kaia.tests.test_marshalling.test_reflector.test_declared_type.setup import T, Basic, Passthrough

class GenericPassthroughTestCase(TestCase):
    def test_with_type(self):
        result = DeclaredType.parse(Passthrough)
        self.assertEqual(DeclaredTypeArgumentKind.type, result.kind)
        self.assertEqual(
            result.mro[0],
            DeclaredTypeMROElement(
                Passthrough,
                Passthrough[object],
                (
                    GenericParameterDescription(T, Annotation.parse(object)),
                ),
            )
        )
        self.assertEqual(
            DeclaredType.parse(Basic[object]).mro,
            result.mro[1:]
        )

    def test_with_generic(self):
        result = DeclaredType.parse(Passthrough[int])
        self.assertEqual(DeclaredTypeArgumentKind.generic_type, result.kind)
        self.assertEqual(
            result.mro[0],
            DeclaredTypeMROElement(
                Passthrough,
                Passthrough[int],
                (
                    GenericParameterDescription(T, Annotation.parse(int)),
                ),
            )
        )
        self.assertEqual(
            DeclaredType.parse(Basic[int]).mro,
            result.mro[1:]
        )

    def test_with_value(self):
        v = Passthrough()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Passthrough).mro,
            result.mro
        )

    def test_with_generic_value(self):
        v = Passthrough[int]()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Passthrough[int]).mro,
            result.mro
        )
