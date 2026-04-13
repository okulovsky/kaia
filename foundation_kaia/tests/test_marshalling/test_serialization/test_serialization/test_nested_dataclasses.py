import unittest
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, Any

from foundation_kaia.marshalling.serialization.handlers.type_handler import SerializationContext
from foundation_kaia.marshalling.serialization.handlers.dataclass_handler import DataclassHandler

def _ctx():
    return SerializationContext(path=[], allow_base64=True)


class Color(Enum):
    RED = 'red'
    GREEN = 'green'
    BLUE = 'blue'


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


# --- Test models ---

@dataclass
class AllPrimitives:
    i: int
    f: float
    s: str
    b: bool
    color: Color
    priority: Priority
    when: datetime


@dataclass
class WithOptionals:
    name: str
    tag: int | None
    label: str | None


@dataclass
class Point:
    x: float
    y: float


@dataclass
class WithContainers:
    names: list[str]
    scores: dict[str, int]
    coords: tuple[float, ...]


@dataclass
class Shape:
    origin: Point
    points: list[Point]
    metadata: dict[str, str]


@dataclass
class TreeNode:
    value: int
    children: list[Any]


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


class TestNestedDataclasses(unittest.TestCase):

    def setUp(self):
        self.desc = DataclassHandler(Shape)

    def test_round_trip(self):
        obj = Shape(
            origin=Point(0.0, 0.0),
            points=[Point(1.0, 2.0), Point(3.0, 4.0)],
            metadata={'color': 'red', 'fill': 'solid'},
        )
        json_data = self.desc.to_json(obj, _ctx())
        restored = self.desc.from_json(json_data, _ctx())
        self.assertEqual(obj, restored)

    def test_json_structure(self):
        obj = Shape(
            origin=Point(5.0, 6.0),
            points=[Point(1.0, 2.0)],
            metadata={},
        )
        json_data = self.desc.to_json(obj, _ctx())
        self.assertEqual(json_data['origin'], {'x': 5.0, 'y': 6.0})
        self.assertEqual(json_data['points'], [{'x': 1.0, 'y': 2.0}])

