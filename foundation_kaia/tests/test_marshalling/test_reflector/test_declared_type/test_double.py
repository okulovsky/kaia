from unittest import TestCase
from foundation_kaia.marshalling.reflector.declared_type import *
from foundation_kaia.marshalling.reflector.annotation import Annotation
from foundation_kaia.tests.test_marshalling.test_reflector.test_declared_type.setup import T, T1, Double

class GenericDoubleTestCase(TestCase):
    def test_with_type(self):
        self.assertEqual(
            DeclaredType(
                DeclaredTypeArgumentKind.type,
                (
                    DeclaredTypeMROElement(
                        Double,
                        Double[object, object],
                        (
                            GenericParameterDescription(T, Annotation.parse(object)),
                            GenericParameterDescription(T1, Annotation.parse(object)),
                        ),
                    ),
                    DeclaredTypeMROElement(
                        object,
                        None,
                        ()
                    ),
                )
            ),
            DeclaredType.parse(Double)
        )

    def test_with_generic(self):
        self.assertEqual(
            DeclaredType(
                DeclaredTypeArgumentKind.generic_type,
                (
                    DeclaredTypeMROElement(
                        Double,
                        Double[int, str],
                        (
                            GenericParameterDescription(T, Annotation.parse(int)),
                            GenericParameterDescription(T1, Annotation.parse(str)),
                        ),
                    ),
                    DeclaredTypeMROElement(
                        object,
                        None,
                        ()
                    ),
                )
            ),
            DeclaredType.parse(Double[int, str])
        )

    def test_with_value(self):
        v = Double()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Double).mro,
            result.mro
        )

    def test_with_generic_value(self):
        v = Double[int, str]()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Double[int, str]).mro,
            result.mro
        )
