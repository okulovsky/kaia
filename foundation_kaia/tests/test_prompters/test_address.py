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



