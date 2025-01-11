from brainbox.framework.common import SignatureProcessor
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
        proc = SignatureProcessor.from_signature(Test.required_only)
        self.assertEqual(('a','b'), proc.mandatory)
        self.assertEqual((), proc.optional)
        self.assertFalse(proc.open)

        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only('a', 'b'))
        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only('a', b='b'))
        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only(a='a', b='b'))

        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a','b','c'))
        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a', a='a'))

        self.assertRaises(Exception, lambda: proc.to_kwargs_only())
        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a'))
        self.assertRaises(Exception, lambda: proc.to_kwargs_only(x='x'))


    def test_required_and_optional(self):
        proc = SignatureProcessor.from_signature(Test.required_and_optional)
        self.assertEqual(('a', 'b'), proc.mandatory)
        self.assertEqual(('c', ), proc.optional)
        self.assertFalse(proc.open)

        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only('a', 'b'))
        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only('a', b='b'))
        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only(a='a', b='b'))

        self.assertDictEqual(dict(a='a', b='b', c='c'), proc.to_kwargs_only('a', 'b', 'c'))
        self.assertDictEqual(dict(a='a', b='b', c='c'), proc.to_kwargs_only('a', 'b', c='c'))
        self.assertDictEqual(dict(a='a', b='b', c='c'), proc.to_kwargs_only('a', b='b', c='c'))
        self.assertDictEqual(dict(a='a', b='b', c='c'), proc.to_kwargs_only(a='a', b='b', c='c'))

        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a','b','c','d'))
        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a', a='a'))

        self.assertRaises(Exception, lambda: proc.to_kwargs_only())
        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a'))
        self.assertRaises(Exception, lambda: proc.to_kwargs_only(a='a', c='c'))


    def test_open(self):
        proc = SignatureProcessor.from_signature(Test.open)
        self.assertEqual(('a', 'b'), proc.mandatory)
        self.assertEqual(('c', ), proc.optional)
        self.assertTrue(proc.open)

        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only('a', 'b'))
        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only('a', b='b'))
        self.assertDictEqual(dict(a='a', b='b'), proc.to_kwargs_only(a='a', b='b'))

        self.assertDictEqual(dict(a='a', b='b', c='c'), proc.to_kwargs_only('a', 'b', 'c'))
        self.assertDictEqual(dict(a='a', b='b', c='c'), proc.to_kwargs_only('a', 'b', c='c'))
        self.assertDictEqual(dict(a='a', b='b', c='c'), proc.to_kwargs_only('a', b='b', c='c'))
        self.assertDictEqual(dict(a='a', b='b', c='c'), proc.to_kwargs_only(a='a', b='b', c='c'))

        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a','b','c','d'))
        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a', a='a'))

        self.assertRaises(Exception, lambda: proc.to_kwargs_only())
        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a'))
        self.assertRaises(Exception, lambda: proc.to_kwargs_only(a='a', c='c'))

        self.assertDictEqual(dict(a='a', b='b', c='c', x='x'), proc.to_kwargs_only(a='a', b='b', c='c', x='x'))
        self.assertRaises(Exception, lambda: proc.to_kwargs_only('a','b','c','d'))



