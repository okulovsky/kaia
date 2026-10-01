from typing import *
from unittest import TestCase
from foundation_kaia.prompters import AddressBuilder,AddressBuilderGC, Address
from foundation_kaia.prompters.address import DefaultElement, GetterOnlyElement
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


class AddressAppendTestCase(TestCase):
    def setUp(self):
        self.obj = MyClass(1, "x", MyClass(2, "y", MyClass(3, "z")))

    def test_append_string(self):
        address = Address.parse("c").append("b")
        self.assertEqual("y", address.get(self.obj))
        self.assertEqual("c.b", str(address))

    def test_append_dotted_string_is_split(self):
        address = Address.parse("c").append("c.a")
        self.assertEqual(3, len(address.address))
        self.assertEqual(3, address.get(self.obj))

    def test_append_element(self):
        address = Address.parse("c").append(DefaultElement("a"))
        self.assertEqual(2, address.get(self.obj))

    def test_append_getter_element(self):
        address = Address.parse("c").append(GetterOnlyElement(lambda o: o.b))
        self.assertEqual("y", address.get(self.obj))

    def test_append_address(self):
        address = Address.parse("c").append(Address.parse("c.b"))
        self.assertEqual(3, len(address.address))
        self.assertEqual("z", address.get(self.obj))

    def test_append_address_builder(self):
        b: MyClass = AddressBuilder()
        address = Address.parse("c").append(b.c.a)
        self.assertEqual(3, address.get(self.obj))

    def test_append_empty_address_changes_nothing(self):
        address = Address.parse("c").append(Address())
        self.assertEqual("c", str(address))

    def test_append_to_empty_address(self):
        address = Address().append("c.a")
        self.assertEqual(2, address.get(self.obj))

    def test_append_does_not_mutate_original(self):
        original = Address.parse("c")
        original.append("b")
        original.append(Address.parse("a"))
        self.assertEqual("c", str(original))
        self.assertEqual(1, len(original.address))

    def test_append_int_index_through_parse(self):
        address = Address.parse(1).append(Address.parse("c")).append("a")
        self.assertEqual("[1].c.a", str(address))
        self.assertEqual(2, address.get([self.obj, self.obj]))

    def test_append_unsupported_raises(self):
        with self.assertRaises(ValueError):
            Address.parse("c").append(5)
        with self.assertRaises(ValueError):
            Address.parse("c").append(None)

    def test_append_then_set(self):
        Address.parse("c").append("c.a").set(self.obj, 99)
        self.assertEqual(99, self.obj.c.c.a)

    def test_append_then_set_on_dict_of_lists(self):
        data = {"items_": [{"v": 1}, {"v": 2}]}
        address = Address.parse("items_").append(Address.parse(1)).append("v")
        address.set(data, 20)
        self.assertEqual(20, data["items_"][1]["v"])
        self.assertEqual(1, data["items_"][0]["v"])


class AddressMiscTestCase(TestCase):
    def test_pop(self):
        address = Address.parse("c.c.a")
        self.assertEqual("c.c", str(address.pop()))
        self.assertTrue(address.pop().pop().pop().is_empty())

    def test_pop_empty_raises(self):
        with self.assertRaises(ValueError):
            Address().pop()

    def test_empty_address_gets_object_itself(self):
        obj = MyClass(1, "x")
        self.assertIs(obj, Address().get(obj))

    def test_set_on_single_element_address(self):
        obj = MyClass(1, "x")
        Address.parse("a").set(obj, 5)
        self.assertEqual(5, obj.a)

    def test_get_only_element_cannot_set(self):
        obj = MyClass(1, "x")
        with self.assertRaises(ValueError):
            Address(lambda o: o.a).set(obj, 5)

    def test_get_failure_reports_address(self):
        with self.assertRaises(ValueError) as ctx:
            Address.parse("c.a").get(MyClass(1, "x"))
        self.assertIn("c.a", str(ctx.exception))

    def test_index_elements(self):
        self.assertEqual("b", Address.parse(1).get(["a", "b"]))
        self.assertEqual("[1]", str(Address.parse(1)))

    def test_parse_sequence_and_address(self):
        self.assertEqual(2, len(Address.parse(["c", "a"]).address))
        original = Address.parse("c.a")
        self.assertEqual("c.a", str(Address.parse(original)))

    def test_pop_several(self):
        address = Address.parse("c.c.a")
        self.assertEqual("c", str(address.pop(2)))
        self.assertTrue(address.pop(3).is_empty())

    def test_pop_zero_returns_equal_address(self):
        address = Address.parse("c.a")
        self.assertEqual("c.a", str(address.pop(0)))

    def test_pop_too_many_raises(self):
        with self.assertRaises(ValueError):
            Address.parse("c.a").pop(3)
        with self.assertRaises(ValueError):
            Address().pop(1)

    def test_pop_negative_raises(self):
        with self.assertRaises(ValueError):
            Address.parse("c.a").pop(-1)

    def test_pop_several_does_not_mutate_original(self):
        address = Address.parse("c.c.a")
        address.pop(2)
        self.assertEqual("c.c.a", str(address))

    def test_pop_several_then_get(self):
        obj = MyClass(1, "x", MyClass(2, "y", MyClass(3, "z")))
        self.assertEqual("y", Address.parse("c.b").append("b").pop(1).get(obj))
        self.assertIs(obj.c, Address.parse("c.c.a").pop(2).get(obj))

