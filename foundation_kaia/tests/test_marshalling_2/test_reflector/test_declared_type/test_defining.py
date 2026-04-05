from unittest import TestCase
from foundation_kaia.marshalling_2.reflector.declared_type import *
from foundation_kaia.tests.test_marshalling_2.test_reflector.test_declared_type.setup import Basic, Defining

class GenericBasicTestCase(TestCase):
    def test_with_type(self):
        result = DeclaredType.parse(Defining)
        self.assertEqual(DeclaredTypeArgumentKind.type, result.kind)
        self.assertEqual(
            result.mro[0],
            DeclaredTypeMROElement(
                Defining,
                None,
                ()
            )
        )
        self.assertEqual(
            DeclaredType.parse(Basic[str]).mro,
            result.mro[1:]
        )

    def test_with_value(self):
        v = Defining()
        result = DeclaredType.parse(v)
        self.assertEqual(DeclaredTypeArgumentKind.value, result.kind)
        self.assertEqual(
            DeclaredType.parse(Defining).mro,
            result.mro
        )
