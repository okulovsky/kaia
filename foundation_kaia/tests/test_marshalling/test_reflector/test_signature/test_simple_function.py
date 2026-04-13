import unittest

from foundation_kaia.marshalling.reflector.signature import Signature, ArgumentKind, FunctionKind


class TestSimpleFunction(unittest.TestCase):

    def test_name_and_callable(self):
        def greet(name: str, count: int) -> str:
            pass

        desc = Signature.parse(greet)
        self.assertEqual(desc.name, 'greet')
        self.assertIs(desc.callable, greet)
        self.assertEqual(desc.kind, FunctionKind.FUNCTION)

    def test_argument_count_and_indices(self):
        def add(a: int, b: int, c: int) -> int:
            pass

        desc = Signature.parse(add)
        self.assertEqual(len(desc.arguments), 3)
        for i, arg in enumerate(desc.arguments):
            self.assertEqual(arg.index, i)
            self.assertEqual(arg.kind, ArgumentKind.POSITIONAL_OR_KEYWORD)

    def test_no_annotation_gives_not_annotated(self):
        def f(x):
            pass

        desc = Signature.parse(f)
        self.assertTrue(desc.arguments[0].annotation.not_annotated)
        self.assertEqual(len(desc.arguments[0].annotation), 0)

    def test_no_return_annotation_gives_not_annotated(self):
        def f(x: int):
            pass

        desc = Signature.parse(f)
        self.assertTrue(desc.returned_type.not_annotated)
        self.assertEqual(len(desc.returned_type), 0)

    def test_lambda(self):
        fn = lambda x, y: x + y  # noqa
        desc = Signature.parse(fn)
        self.assertEqual(desc.name, '<lambda>')
        self.assertEqual(desc.kind, FunctionKind.LAMBDA)
        self.assertEqual(len(desc.arguments), 2)

    def test_has_default_property(self):
        def f(a: int, b: str = 'x') -> None:
            pass

        desc = Signature.parse(f)
        self.assertFalse(desc.arguments[0].has_default)
        self.assertTrue(desc.arguments[1].has_default)

    def test_default_value_stored(self):
        def f(a: int, b: str = 'hello', c: float = 3.14) -> None:
            pass

        desc = Signature.parse(f)
        self.assertEqual(desc.arguments[1].default, 'hello')
        self.assertEqual(desc.arguments[2].default, 3.14)


if __name__ == '__main__':
    unittest.main()
