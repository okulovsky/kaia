import unittest
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, Any

from foundation_kaia.marshalling_2.serialization.handlers.type_handler import SerializationContext
from foundation_kaia.marshalling_2.serialization.handlers.dataclass_handler import DataclassHandler

def _ctx():
    return SerializationContext(path=[], allow_base64=True)


@dataclass
class Animal:
    name: str


@dataclass
class Dog(Animal):
    breed: str


@dataclass
class Cat(Animal):
    indoor: bool


@dataclass
class Shelter:
    location: str
    mascot: Animal
    residents: list[Animal]




class TestPolymorphism(unittest.TestCase):

    def setUp(self):
        self.desc = DataclassHandler(Shelter)

    def test_subclass_in_base_field(self):
        """A Dog in an Animal-typed field gets @type tag and round-trips."""
        obj = Shelter(
            location='downtown',
            mascot=Dog(name='Rex', breed='labrador'),
            residents=[],
        )
        json_data = self.desc.to_json(obj, _ctx())
        self.assertIn('@type', json_data['mascot'])
        self.assertEqual(json_data['mascot']['name'], 'Rex')
        self.assertEqual(json_data['mascot']['breed'], 'labrador')
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)
        self.assertIsInstance(restored.mascot, Dog)

    def test_exact_base_no_type_tag(self):
        """An Animal instance (not a subclass) serializes without @type."""
        obj = Shelter(
            location='uptown',
            mascot=Animal(name='Buddy'),
            residents=[],
        )
        json_data = self.desc.to_json(obj, _ctx())
        self.assertNotIn('@type', json_data['mascot'])
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

    def test_mixed_subclasses_in_list(self):
        """A list[Animal] can hold Dogs and Cats, all round-trip correctly."""
        obj = Shelter(
            location='suburb',
            mascot=Animal(name='Logo'),
            residents=[
                Dog(name='Fido', breed='poodle'),
                Cat(name='Whiskers', indoor=True),
                Animal(name='Generic'),
                Cat(name='Shadow', indoor=False),
            ],
        )
        json_data = self.desc.to_json(obj, _ctx())
        # Subclasses get @type, base class does not
        self.assertIn('@type', json_data['residents'][0])
        self.assertIn('@type', json_data['residents'][1])
        self.assertNotIn('@type', json_data['residents'][2])
        self.assertIn('@type', json_data['residents'][3])
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)
        self.assertIsInstance(restored.residents[0], Dog)
        self.assertIsInstance(restored.residents[1], Cat)
        self.assertIsInstance(restored.residents[2], Animal)
        self.assertIsInstance(restored.residents[3], Cat)

    def test_type_tag_contains_full_class_name(self):
        """@type is 'dataclass'; @subtype holds the fully qualified class name."""
        obj = Shelter(
            location='x',
            mascot=Dog(name='D', breed='b'),
            residents=[],
        )
        json_data = self.desc.to_json(obj, _ctx())
        self.assertEqual(json_data['mascot']['@type'], 'dataclass')
        subtype_tag = json_data['mascot']['@subtype']
        self.assertIn('Dog', subtype_tag)
        self.assertIn('.', subtype_tag)

    def test_wrong_type_token_raises_clear_error(self):
        """Passing a dict with @type set to an unexpected token raises a clear TypeError."""
        json_with_wrong_token = {'@type': 'sqlalchemy', '@subtype': 'some.Class', 'name': 'Rex'}
        with self.assertRaises(TypeError) as ctx:
            self.desc.from_json({'mascot': json_with_wrong_token, 'location': 'x', 'residents': []}, _ctx())
        self.assertIn('dataclass', str(ctx.exception))
        self.assertIn('sqlalchemy', str(ctx.exception))

