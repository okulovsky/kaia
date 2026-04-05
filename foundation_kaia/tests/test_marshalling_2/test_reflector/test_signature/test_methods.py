import unittest
from foundation_kaia.marshalling_2.reflector.signature import Signature, ArgumentKind, FunctionKind


class Greeter:
    def greet(self, name: str, loud: bool = False) -> str:
        pass

    @classmethod
    def from_config(cls, path: str) -> 'Greeter':
        pass

    @staticmethod
    def default_greeting() -> str:
        pass


class Child(Greeter):
    def greet(self, name: str, loud: bool = False, *, emoji: str = '') -> str:
        pass


class TestMethods(unittest.TestCase):

    def test_instance_method_unbound(self):
        desc = Signature.parse(Greeter.greet)
        self.assertEqual(desc.name, 'greet')
        self.assertEqual(desc.kind, FunctionKind.INSTANCE_METHOD)
        self.assertEqual(len(desc.arguments), 3)
        self.assertEqual(desc.arguments[0].name, 'self')
        self.assertEqual(desc.arguments[0].index, 0)
        self.assertTrue(desc.arguments[0].annotation.not_annotated)
        self.assertEqual(desc.arguments[1].name, 'name')
        self.assertEqual(desc.arguments[1].index, 1)

    def test_instance_method_bound(self):
        obj = Greeter()
        desc = Signature.parse(obj.greet)
        self.assertEqual(desc.kind, FunctionKind.INSTANCE_METHOD)
        # bound method: self is not in the signature
        self.assertEqual(desc.arguments[0].name, 'name')
        self.assertEqual(desc.arguments[0].index, 0)

    def test_classmethod(self):
        desc = Signature.parse(Greeter.from_config)
        self.assertEqual(desc.kind, FunctionKind.CLASS_METHOD)
        self.assertEqual(desc.arguments[0].name, 'path')
        self.assertEqual(desc.arguments[0].index, 0)

    def test_staticmethod(self):
        desc = Signature.parse(Greeter.default_greeting)
        self.assertEqual(desc.kind, FunctionKind.STATIC_METHOD)
        self.assertEqual(len(desc.arguments), 0)
        self.assertEqual(desc.name, 'default_greeting')

    def test_inherited_method(self):
        desc = Signature.parse(Child.greet)
        self.assertEqual(desc.kind, FunctionKind.INSTANCE_METHOD)
        self.assertEqual(len(desc.arguments), 4)
        self.assertEqual(desc.arguments[3].name, 'emoji')
        self.assertEqual(desc.arguments[3].kind, ArgumentKind.KEYWORD_ONLY)
        self.assertIsNone(desc.arguments[3].index)

    def test_dunder_init(self):
        class Config:
            def __init__(self, host: str, port: int, debug: bool = False):
                pass

        desc = Signature.parse(Config.__init__)
        self.assertEqual(desc.name, '__init__')
        self.assertEqual(desc.kind, FunctionKind.INSTANCE_METHOD)
        self.assertEqual(desc.arguments[0].name, 'self')
        self.assertEqual(desc.arguments[1].name, 'host')
        self.assertEqual(desc.arguments[2].name, 'port')
        self.assertEqual(desc.arguments[3].name, 'debug')

    def test_dataclass_init(self):
        from dataclasses import dataclass

        @dataclass
        class Point:
            x: float
            y: float

        desc = Signature.parse(Point.__init__)
        self.assertEqual(desc.kind, FunctionKind.INSTANCE_METHOD)
        self.assertEqual(desc.arguments[0].name, 'self')
        self.assertEqual(desc.arguments[1].name, 'x')
        self.assertEqual(desc.arguments[2].name, 'y')


if __name__ == '__main__':
    unittest.main()
