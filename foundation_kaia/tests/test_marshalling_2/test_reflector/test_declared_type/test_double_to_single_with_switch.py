from unittest import TestCase
from foundation_kaia.marshalling_2.reflector.declared_type import *
from foundation_kaia.marshalling_2.reflector.annotation import Annotation
from foundation_kaia.tests.test_marshalling_2.test_reflector.test_declared_type.setup import T, Double, DoubleToSingleWithSwitch

class GenericDoubleToSingleWithSwitchTestCase(TestCase):
    def test_with_type(self):
        result = DeclaredType.parse(DoubleToSingleWithSwitch)
        self.assertEqual(DeclaredTypeArgumentKind.type, result.kind)
        self.assertEqual(
            result.mro[0],
            DeclaredTypeMROElement(
                DoubleToSingleWithSwitch,
                DoubleToSingleWithSwitch[object],
                (
                    GenericParameterDescription(T, Annotation.parse(object)),
                ),
            )
        )
        self.assertEqual(
            DeclaredType.parse(Double[list[int], object]).mro,
            result.mro[1:]
        )

    def test_with_generic(self):
        result = DeclaredType.parse(DoubleToSingleWithSwitch[str])
        self.assertEqual(DeclaredTypeArgumentKind.generic_type, result.kind)
        self.assertEqual(
            result.mro[0],
            DeclaredTypeMROElement(
                DoubleToSingleWithSwitch,
                DoubleToSingleWithSwitch[str],
                (
                    GenericParameterDescription(T, Annotation.parse(str)),
                ),
            )
        )
        self.assertEqual(
            DeclaredType.parse(Double[list[int], str]).mro,
            result.mro[1:]
        )

    def test_with_value(self):
        v = DoubleToSingleWithSwitch()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(DoubleToSingleWithSwitch).mro,
            result.mro
        )

    def test_with_generic_value(self):
        v = DoubleToSingleWithSwitch[str]()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(DoubleToSingleWithSwitch[str]).mro,
            result.mro
        )
