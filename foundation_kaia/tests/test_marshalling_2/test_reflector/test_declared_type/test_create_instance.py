from unittest import TestCase
from foundation_kaia.marshalling_2.reflector import DeclaredType, Annotation
from typing import Generic, TypeVar
from dataclasses import dataclass

T = TypeVar('T')


class NoArgs:
    pass


class WithArgs:
    def __init__(self, x: int, y: str = 'default'):
        self.x = x
        self.y = y

@dataclass
class Dataclass:
    x: int = 4

class GenericClass(Generic[T]):
    pass


class CreateInstanceTestCase(TestCase):
    def test_no_args(self):
        instance = DeclaredType.parse(NoArgs).create_instance()
        self.assertIsInstance(instance, NoArgs)

    def test_with_args(self):
        instance = DeclaredType.parse(WithArgs).create_instance(42)
        self.assertIsInstance(instance, WithArgs)
        self.assertEqual(42, instance.x)
        self.assertEqual('default', instance.y)

    def test_with_kwargs(self):
        instance = DeclaredType.parse(WithArgs).create_instance(x=7, y='hello')
        self.assertIsInstance(instance, WithArgs)
        self.assertEqual(7, instance.x)
        self.assertEqual('hello', instance.y)

    def test_dataclass(self):
        instance = DeclaredType.parse(Dataclass).create_instance()
        self.assertIsInstance(instance, Dataclass)
        self.assertEqual(4, instance.x)

    def test_generic_class(self):
        instance = DeclaredType.parse(GenericClass[int]).create_instance()
        self.assertIsInstance(instance, GenericClass)
        annotation = Annotation.parse(instance)
        self.assertEqual(int, annotation.types[0].self.parameters[0].generic_parameter_value.types[0].self.type)


