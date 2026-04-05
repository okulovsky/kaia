import unittest

from foundation_kaia.marshalling_2.reflector.signature import Signature


class TestAssignBasic(unittest.TestCase):

    def test_positional_args(self):
        def f(a: int, b: str, c: float) -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(1, 'hello', 3.14)
        self.assertEqual(result, {'a': 1, 'b': 'hello', 'c': 3.14})

    def test_keyword_args(self):
        def f(a: int, b: str) -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(a=10, b='world')
        self.assertEqual(result, {'a': 10, 'b': 'world'})

    def test_mixed_positional_and_keyword(self):
        def f(a: int, b: str, c: float) -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(1, c=3.14, b='hi')
        self.assertEqual(result, {'a': 1, 'b': 'hi', 'c': 3.14})

    def test_no_arguments(self):
        def f() -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names()
        self.assertEqual(result, {})


class TestDefaults(unittest.TestCase):

    def test_partial_args_without_defaults_raises(self):
        def f(a: int, b: str, c: float) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(1)
        self.assertIn('missing required arguments', str(cm.exception))
        self.assertIn("'b'", str(cm.exception))
        self.assertIn("'c'", str(cm.exception))

    def test_partial_args_with_defaults_ok(self):
        def f(a: int, b: str = 'a', c: float = 13.0) -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(1, 'b')
        self.assertEqual(result, {'a': 1, 'b': 'b'})

    def test_only_required_provided(self):
        def f(a: int, b: str = 'default') -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(1)
        self.assertEqual(result, {'a': 1})

    def test_all_defaults_none_provided(self):
        def f(a: int = 0, b: str = '') -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names()
        self.assertEqual(result, {})

    def test_default_overridden(self):
        def f(a: int, b: str = 'default') -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(1, 'override')
        self.assertEqual(result, {'a': 1, 'b': 'override'})

    def test_keyword_only_with_default(self):
        def f(a: int, *, key: str = 'x') -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(1)
        self.assertEqual(result, {'a': 1})

    def test_keyword_only_without_default_missing_raises(self):
        def f(a: int, *, key: str) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(1)
        self.assertIn("'key'", str(cm.exception))

    def test_none_as_default_is_valid(self):
        def f(a: int, b: str | None = None) -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(1)
        self.assertEqual(result, {'a': 1})


class TestKeywordOnly(unittest.TestCase):

    def test_keyword_only_params(self):
        def f(a: int, *, key: str, flag: bool) -> None:
            pass

        desc = Signature.parse(f)
        result = desc.assign_parameters_to_names(1, key='x', flag=True)
        self.assertEqual(result, {'a': 1, 'key': 'x', 'flag': True})

    def test_keyword_only_cannot_be_positional(self):
        def f(*, key: str) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names('oops')
        self.assertIn('0 positional arguments', str(cm.exception))


class TestPositionalOnly(unittest.TestCase):

    def test_positional_only_raises(self):
        def f(a: int, b: str, /) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(1, 'hi')
        self.assertIn('positional-only', str(cm.exception))
        self.assertIn("'a'", str(cm.exception))

    def test_mixed_positional_only_and_regular_still_raises(self):
        def f(a: int, /, b: str = 'x') -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(1)
        self.assertIn('positional-only', str(cm.exception))


class TestExtraArguments(unittest.TestCase):

    def test_too_many_positional(self):
        def f(a: int) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(1, 2, 3)
        self.assertIn('1 positional arguments', str(cm.exception))
        self.assertIn('3 were given', str(cm.exception))

    def test_unexpected_keyword(self):
        def f(a: int) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(a=1, z=99)
        self.assertIn("unexpected keyword argument 'z'", str(cm.exception))

    def test_duplicate_arg(self):
        def f(a: int, b: str) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(1, a=2)
        self.assertIn("multiple values for argument 'a'", str(cm.exception))


class TestVarPositionalRejected(unittest.TestCase):

    def test_var_positional_raises(self):
        def f(a: int, *args: float) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(1, 2.0)
        self.assertIn('*args', str(cm.exception))

    def test_var_positional_only_raises(self):
        def f(*args: str) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names('a')
        self.assertIn('*args', str(cm.exception))


class TestVarKeywordRejected(unittest.TestCase):

    def test_var_keyword_raises(self):
        def f(a: int, **kwargs: str) -> None:
            pass

        desc = Signature.parse(f)
        with self.assertRaises(TypeError) as cm:
            desc.assign_parameters_to_names(1)
        self.assertIn('**kwargs', str(cm.exception))


class TestInstanceMethod(unittest.TestCase):

    def test_skips_self(self):
        class MyClass:
            def method(self, a: int, b: str) -> None:
                pass

        desc = Signature.parse(MyClass.method)
        result = desc.assign_parameters_to_names(1, b='hi')
        self.assertEqual(result, {'a': 1, 'b': 'hi'})

    def test_skips_first_arg_regardless_of_name(self):
        class MyClass:
            def method(this, a: int, b: str) -> None:
                pass

        desc = Signature.parse(MyClass.method)
        result = desc.assign_parameters_to_names(1, b='hi')
        self.assertEqual(result, {'a': 1, 'b': 'hi'})

    def test_self_not_assignable(self):
        class MyClass:
            def method(self, a: int) -> None:
                pass

        desc = Signature.parse(MyClass.method)
        with self.assertRaises(TypeError):
            desc.assign_parameters_to_names(a=1, self='bad')


if __name__ == '__main__':
    unittest.main()
