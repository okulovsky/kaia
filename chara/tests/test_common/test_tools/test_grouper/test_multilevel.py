# test_grouper.py

import unittest
from dataclasses import dataclass
from chara.common.tools.core.grouper import Grouper, Reply, Selector


@dataclass
class DummyDrawable:
    """
    Minimal stub for IDrawable.
    Selectors will access these attributes.
    """
    category: str
    subcategory: str
    name: str

class TestGrouperMultiLevel(unittest.TestCase):
    def setUp(self):
        # 3 distinct (category, subcategory) combinations
        self.d1 = DummyDrawable("A", "x", "d1")
        self.d2 = DummyDrawable("A", "y", "d2")
        self.d3 = DummyDrawable("B", "x", "d3")
        self.drawables = [self.d1, self.d2, self.d3]

        self.category_selector = Selector(lambda d: d.category)
        self.subcategory_selector = Selector(lambda d: d.subcategory)

    def test_two_level_grouping(self):
        """
        With two selectors, we expect a hierarchy:

        category=A
          sub=x -> [d1]
          sub=y -> [d2]
        category=B
          sub=x -> [d3]

        Emitted sequence (keys sorted within each level):

        Reply("A", 0, None)
        Reply("x", 1, None)
        Reply(None, None, [d1])
        Reply("y", 1, None)
        Reply(None, None, [d2])
        Reply("B", 0, None)
        Reply("x", 1, None)
        Reply(None, None, [d3])
        """
        grouper = Grouper(
            selectors=[self.category_selector, self.subcategory_selector]
        )

        replies = list(grouper.group(self.drawables))

        # For convenience, summarize what we got:
        summary = [
            (r.group_key, r.group_level, None if r.drawables is None else [d.name for d in r.drawables])
            for r in replies
        ]

        expected = [
            ("A", 0, None),
            ("x", 1, None),
            (None, None, ["d1"]),
            ("y", 1, None),
            (None, None, ["d2"]),
            ("B", 0, None),
            ("x", 1, None),
            (None, None, ["d3"]),
        ]

        self.assertEqual(summary, expected)

    def test_key_sorting_at_each_level(self):
        """
        Keys at each level should be iterated in sorted order.
        We shuffle input drawables and still expect A before B, x before y.
        """
        shuffled = [self.d3, self.d2, self.d1]
        grouper = Grouper(
            selectors=[self.category_selector, self.subcategory_selector]
        )
        replies = list(grouper.group(shuffled))

        keys_levels = [(r.group_key, r.group_level) for r in replies if r.drawables is None]

        expected_keys_levels = [
            ("A", 0),
            ("x", 1),
            ("y", 1),
            ("B", 0),
            ("x", 1),
        ]

        self.assertEqual(keys_levels, expected_keys_levels)


if __name__ == "__main__":
    unittest.main()
