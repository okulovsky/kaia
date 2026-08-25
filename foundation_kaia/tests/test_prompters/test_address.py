from typing import *
from unittest import TestCase
from foundation_kaia.prompters import AddressBuilder,AddressBuilderGC, Address
from dataclasses import dataclass



@dataclass
class MyClass:
    a: int
    b: str
    c: Optional['MyClass'] = None

class AddressBuilderTestCase(TestCase):
    def test_access(self):
        b: MyClass = AddressBuilder()
        result = b.c.c.a
        key = result.__str__()[2:-2]
        address = AddressBuilderGC.find(AddressBuilderGC.Dimension.address, key)
        self.assertIsNotNone(address)
        self.assertEqual(3, len(address.address))
        self.assertEqual('c', address.address[0].element)
        self.assertEqual('c', address.address[1].element)
        self.assertEqual('a', address.address[2].element)


    def test_string_definition(self):
        obj = MyClass(45, "34", MyClass(12, "23"))
        self.assertEqual(45, Address.parse("a").get(obj))
        self.assertEqual("23", Address.parse("c.b").get(obj))
        self.assertEqual("23", Address.parse(lambda q: q.c.b).get(obj))

    def test_set_on_setitem_target(self):
        # DefaultElement.set used to call the already-bound `__setitem__` with `obj`
        # as an extra leading argument (setitem(obj, self.element, value)), which
        # TypeErrors for any object that only supports item access (no matching
        # attribute name), e.g. a plain dict.
        obj = {}
        Address.parse("a").set(obj, 45)
        self.assertEqual({"a": 45}, obj)

    def test_set_on_setitem_target_nested(self):
        inner = {}
        outer = {"c": inner}
        Address.parse("c.b").set(outer, "23")
        self.assertEqual({"b": "23"}, inner)



