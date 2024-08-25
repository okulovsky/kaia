from kaia.brainbox.core.small_classes.arguments_validator import ArgumentsValidator
from unittest import TestCase

class Test:
    def required_only(self, a, b):
        pass

    def required_and_optional(self, a, b, c=None):
        pass

    def open(self, a, b, c=None, **kwargs):
        pass


class ArgumentsValidatorTestCase(TestCase):
    def test_required_only(self):
        ArgumentsValidator.from_signature(Test.required_only).validate(['a','b'])
        self.assertRaises(
            Exception,
            lambda: ArgumentsValidator.from_signature(Test.required_only).validate(['a','b', 'c'])
        )
        self.assertRaises(
            Exception,
            lambda: ArgumentsValidator.from_signature(Test.required_only).validate(['a'])
        )

    def test_required_and_optional(self):
        ArgumentsValidator.from_signature(Test.required_and_optional).validate(['a', 'b'])
        ArgumentsValidator.from_signature(Test.required_and_optional).validate(['a', 'b', 'c'])

        self.assertRaises(
            Exception,
            lambda: ArgumentsValidator.from_signature(Test.required_only).validate(['a','b', 'd'])
        )

        self.assertRaises(
            Exception,
            lambda: ArgumentsValidator.from_signature(Test.required_only).validate(['a', 'c'])
        )

    def test_open(self):
        ArgumentsValidator.from_signature(Test.open).validate(['a', 'b'])
        ArgumentsValidator.from_signature(Test.open).validate(['a', 'b', 'c'])
        ArgumentsValidator.from_signature(Test.open).validate(['a', 'b', 'c','d','e','f'])

        self.assertRaises(
            Exception,
            lambda: ArgumentsValidator.from_signature(Test.open).validate(['a', 'c'])
        )