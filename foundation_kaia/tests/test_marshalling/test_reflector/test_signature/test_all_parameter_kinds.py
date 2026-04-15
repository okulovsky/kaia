import unittest
from foundation_kaia.marshalling.reflector.signature import Signature, ArgumentKind


class TestAllParameterKinds(unittest.TestCase):

    def test_positional_only(self):
        def f(a: int, b: str, /):
            pass

        desc = Signature.parse(f)
        self.assertEqual(desc.arguments[0].kind, ArgumentKind.POSITIONAL_ONLY)
        self.assertEqual(desc.arguments[0].index, 0)
        self.assertEqual(desc.arguments[1].kind, ArgumentKind.POSITIONAL_ONLY)
        self.assertEqual(desc.arguments[1].index, 1)

    def test_keyword_only(self):
        def f(*, key: bool, label: str):
            pass

        desc = Signature.parse(f)
        self.assertEqual(len(desc.arguments), 2)
        self.assertEqual(desc.arguments[0].kind, ArgumentKind.KEYWORD_ONLY)
        self.assertIsNone(desc.arguments[0].index)
        self.assertEqual(desc.arguments[1].kind, ArgumentKind.KEYWORD_ONLY)
        self.assertIsNone(desc.arguments[1].index)

    def test_var_positional(self):
        def f(a: int, *args: float):
            pass

        desc = Signature.parse(f)
        self.assertEqual(desc.arguments[0].kind, ArgumentKind.POSITIONAL_OR_KEYWORD)
        self.assertEqual(desc.arguments[0].index, 0)
        self.assertEqual(desc.arguments[1].name, 'args')
        self.assertEqual(desc.arguments[1].kind, ArgumentKind.VAR_POSITIONAL)
        self.assertEqual(desc.arguments[1].index, 1)

    def test_var_keyword(self):
        def f(**kwargs: str):
            pass

        desc = Signature.parse(f)
        self.assertEqual(len(desc.arguments), 1)
        self.assertEqual(desc.arguments[0].name, 'kwargs')
        self.assertEqual(desc.arguments[0].kind, ArgumentKind.VAR_KEYWORD)
        self.assertIsNone(desc.arguments[0].index)

    def test_all_kinds_together(self):
        def f(a: int, /, b: str, *args: float, key: bool = True, **kwargs: str) -> None:
            pass

        desc = Signature.parse(f)
        self.assertEqual(len(desc.arguments), 5)
        a, b, args, key, kwargs = desc.arguments

        self.assertEqual(a.kind, ArgumentKind.POSITIONAL_ONLY)
        self.assertEqual(a.index, 0)

        self.assertEqual(b.kind, ArgumentKind.POSITIONAL_OR_KEYWORD)
        self.assertEqual(b.index, 1)

        self.assertEqual(args.kind, ArgumentKind.VAR_POSITIONAL)
        self.assertEqual(args.index, 2)

        self.assertEqual(key.kind, ArgumentKind.KEYWORD_ONLY)
        self.assertIsNone(key.index)

        self.assertEqual(kwargs.kind, ArgumentKind.VAR_KEYWORD)
        self.assertIsNone(kwargs.index)


if __name__ == '__main__':
    unittest.main()
