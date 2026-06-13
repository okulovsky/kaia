import unittest
from dataclasses import dataclass
from chara.common.tools.drawing.drawer.selector import Selector
from foundation_kaia.prompters import Referrer


@dataclass
class Item:
    name: str
    category: str


class SelectorTestCase(unittest.TestCase):

    # --- Lambda works on both metadata types ---

    def test_lambda_on_dict_metadata(self):
        metadata = {'col': 'X', 'row': 'A'}
        self.assertEqual('X', Selector(lambda m: m['col']).get(metadata))

    def test_lambda_on_object_metadata(self):
        metadata = Item(name='apple', category='fruit')
        self.assertEqual('fruit', Selector(lambda m: m.category).get(metadata))

    # --- String key on dict metadata (IDrawable case): uses __getitem__ ---

    def test_string_on_dict_resolves_by_key(self):
        metadata = {'col': 'X', 'row': 'A'}
        self.assertEqual('X', Selector('col').get(metadata))
        self.assertEqual('A', Selector('row').get(metadata))

    def test_string_on_dict_missing_key_raises(self):
        with self.assertRaises(Exception):
            Selector('missing').get({'col': 'X'})

    # --- String key on object metadata (plain class case): uses getattr ---

    def test_string_on_object_resolves_by_attribute(self):
        metadata = Item(name='apple', category='fruit')
        self.assertEqual('apple', Selector('name').get(metadata))
        self.assertEqual('fruit', Selector('category').get(metadata))

    def test_string_on_object_missing_attribute_raises(self):
        with self.assertRaises(Exception):
            Selector('missing').get(Item(name='apple', category='fruit'))

    # --- Attribute takes priority over __getitem__ when both present ---

    def test_attribute_takes_priority_over_getitem(self):
        # dict has __getitem__, but 'keys' is also an attribute on dict
        metadata = {'col': 'X'}
        result = Selector('keys').get(metadata)
        self.assertTrue(callable(result))  # dict.keys method, not a key lookup

    def test_referrer(self):
        metadata = Item(name='apple', category='fruit')
        ref = Referrer[Item]().ref
        self.assertEqual('apple', Selector(ref.name).get(metadata))
