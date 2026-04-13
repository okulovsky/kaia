from unittest import TestCase
from foundation_kaia.marshalling.reflector import *
from foundation_kaia.tests.test_marshalling.test_reflector.test_declared_type.setup import T, Basic


class GenericBasicTestCase(TestCase):
    def test_with_type(self):
        self.assertEqual(
            DeclaredType(
                DeclaredTypeArgumentKind.type,
                (
                    DeclaredTypeMROElement(
                        Basic,
                        Basic[object],
                        (
                            GenericParameterDescription(T,Annotation.parse(object)),
                        ),
                    ),
                    DeclaredTypeMROElement(
                        object,
                        None,
                        ()
                    ),
                )
            ),
            DeclaredType.parse(Basic)
        )

    def test_with_generic(self):
        self.assertEqual(
            DeclaredType(
                DeclaredTypeArgumentKind.generic_type,
                (
                    DeclaredTypeMROElement(
                        Basic,
                        Basic[int],
                        (
                            GenericParameterDescription(T, Annotation.parse(int)),
                        ),
                    ),
                    DeclaredTypeMROElement(
                        object,
                        None,
                        ()
                    ),
                )
            ),
            DeclaredType.parse(Basic[int])
        )

    def test_with_value(self):
        v = Basic()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Basic).mro,
            result.mro
        )

    def test_with_generic_value(self):
        v = Basic[int]()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Basic[int]).mro,
            result.mro
        )


