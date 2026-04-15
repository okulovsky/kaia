import unittest
from foundation_kaia.marshalling import (
    endpoint, HttpMethod, EndpointAttributes, ENDPOINT_ATTR,
)


class TestVerifyAbstract(unittest.TestCase):

    def test_stub_body_ellipsis_accepted(self):
        @endpoint
        def my_ep(self, x: int) -> str: ...
        self.assertTrue(hasattr(my_ep, ENDPOINT_ATTR))

    def test_stub_body_pass_accepted(self):
        @endpoint
        def my_ep(self, x: int) -> str:
            pass
        self.assertTrue(hasattr(my_ep, ENDPOINT_ATTR))

    def test_real_body_rejected_by_default(self):
        with self.assertRaises(TypeError):
            @endpoint
            def my_ep(self, x: int) -> str:
                return str(x)

    def test_real_body_accepted_with_verify_abstract_false(self):
        @endpoint(verify_abstract=False)
        def my_ep(self, x: int) -> str:
            return str(x)
        self.assertTrue(hasattr(my_ep, ENDPOINT_ATTR))

    def test_stub_raises_not_implemented(self):
        @endpoint
        def my_ep(self, x: int) -> str: ...
        with self.assertRaises(NotImplementedError):
            my_ep(None, 1)

    def test_name_preserved(self):
        @endpoint
        def some_name(self) -> None: ...
        self.assertEqual(some_name.__name__, 'some_name')

    def test_annotations_preserved(self):
        @endpoint
        def my_ep(self, x: int) -> str: ...
        self.assertIn('x', my_ep.__annotations__)
        self.assertIn('return', my_ep.__annotations__)

    def test_works_without_self(self):
        @endpoint
        def my_ep(x: int) -> str: ...
        self.assertTrue(hasattr(my_ep, ENDPOINT_ATTR))


class TestDecoratorAttributes(unittest.TestCase):

    def test_defaults(self):
        @endpoint
        def my_ep(self) -> None: ...
        attrs: EndpointAttributes = getattr(my_ep, ENDPOINT_ATTR)
        self.assertEqual(attrs.method, HttpMethod.POST)
        self.assertIsNone(attrs.content_type)
        self.assertTrue(attrs.verify_abstract)

    def test_get_method_string(self):
        @endpoint(method='GET', verify_abstract=False)
        def my_ep(self, x: int) -> int:
            return x
        attrs: EndpointAttributes = getattr(my_ep, ENDPOINT_ATTR)
        self.assertEqual(attrs.method, HttpMethod.GET)

    def test_get_method_enum(self):
        @endpoint(method=HttpMethod.GET, verify_abstract=False)
        def my_ep(self, x: int) -> int:
            return x
        attrs: EndpointAttributes = getattr(my_ep, ENDPOINT_ATTR)
        self.assertEqual(attrs.method, HttpMethod.GET)

    def test_content_type(self):
        @endpoint(content_type='application/octet-stream')
        def my_ep(self) -> None: ...
        attrs: EndpointAttributes = getattr(my_ep, ENDPOINT_ATTR)
        self.assertEqual(attrs.content_type, 'application/octet-stream')

    def test_bare_decorator(self):
        """@endpoint without parentheses works."""
        @endpoint
        def my_ep(self) -> None: ...
        self.assertTrue(hasattr(my_ep, ENDPOINT_ATTR))

    def test_decorator_with_parens_no_args(self):
        """@endpoint() with parentheses but no args works."""
        @endpoint()
        def my_ep(self) -> None: ...
        self.assertTrue(hasattr(my_ep, ENDPOINT_ATTR))


class TestAttributePropagation(unittest.TestCase):

    def test_custom_dict_attribute_propagates_through_stub(self):
        """functools.update_wrapper copies __dict__, so any attribute set on the
        original function before @endpoint is applied must survive on the stub."""
        def my_ep(self, x: int) -> str: ...
        my_ep.__custom_marker__ = ['some', 'data']

        stub = endpoint(my_ep)

        self.assertTrue(hasattr(stub, '__custom_marker__'))
        self.assertEqual(['some', 'data'], stub.__custom_marker__)

    def test_attribute_set_after_endpoint_does_not_affect_original(self):
        """Propagation is a copy, not a live reference."""
        def my_ep(self, x: int) -> str: ...
        my_ep.__custom_marker__ = 'original'
        stub = endpoint(my_ep)

        stub.__custom_marker__ = 'changed'

        self.assertEqual('original', my_ep.__custom_marker__)


if __name__ == '__main__':
    unittest.main()
