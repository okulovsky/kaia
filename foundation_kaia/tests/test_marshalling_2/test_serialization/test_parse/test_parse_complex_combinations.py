import unittest
from foundation_kaia.marshalling_2.serialization import (
    Serializer, IntHandler, StringHandler, ListHandler, DictHandler,
)


class TestParseNested(unittest.TestCase):

    def test_list_of_dicts(self):
        result = Serializer.parse(list[dict[str, int]])
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertIsInstance(desc.element_serializer.handlers[0], DictHandler)

    def test_dict_of_lists(self):
        result = Serializer.parse(dict[str, list[int]])
        desc = result.handlers[0]
        self.assertIsInstance(desc, DictHandler)
        self.assertIsInstance(desc.value_serializer.handlers[0], ListHandler)

    def test_union_of_containers(self):
        result = Serializer.parse(list[int] | dict[str, int])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {ListHandler, DictHandler})

    def test_list_of_union(self):
        result = Serializer.parse(list[int | str])
        desc = result.handlers[0]
        self.assertIsInstance(desc, ListHandler)
        self.assertEqual(len(desc.element_serializer.handlers), 2)
        types = {type(h) for h in desc.element_serializer.handlers}
        self.assertEqual(types, {IntHandler, StringHandler})


if __name__ == '__main__':
    unittest.main()
