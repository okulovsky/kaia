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


class TestGrouperBasic(unittest.TestCase):
    def test_group_no_selectors_returns_single_leaf(self):
        """
        If no selectors are provided, group() should just return
        a single Reply containing all drawables.
        """
        drawables = [
            DummyDrawable("A", "x", "d1"),
            DummyDrawable("A", "y", "d2"),
        ]
        grouper = Grouper(selectors=[])

        replies = list(grouper.group(drawables))

        self.assertEqual(len(replies), 1)
        leaf = replies[0]
        self.assertIsInstance(leaf, Reply)
        self.assertIsNone(leaf.group_key)
        self.assertIsNone(leaf.group_level)
        self.assertEqual(leaf.drawables, drawables)



    def test_single_selector_groups_by_key(self):

        drawables = [
            DummyDrawable("A", "x", "d1"),
            DummyDrawable("A", "y", "d2"),
            DummyDrawable("B", "x", "d3"),
        ]
        """
        With a single selector, group() should:
        - emit a group Reply for each distinct key (sorted by key),
        - then a leaf Reply with the drawables of that group.
        """
        grouper = Grouper(selectors=[Selector(lambda d: d.category)])

        replies = list(grouper.group(drawables))

        # We expect keys A then B (sorted)
        # Pattern:
        #   Reply("A", 0, None)
        #   Reply(None, None, [d1, d2])
        #   Reply("B", 0, None)
        #   Reply(None, None, [d3])

        self.assertEqual(len(replies), 4)

        # A group
        self.assertEqual(replies[0].group_key, "A")
        self.assertEqual(replies[0].group_level, 0)
        self.assertIsNone(replies[0].drawables)

        # A leaf
        self.assertIsNone(replies[1].group_key)
        self.assertIsNone(replies[1].group_level)
        self.assertEqual(
            [d.name for d in replies[1].drawables],
            ["d1", "d2"],
        )

        # B group
        self.assertEqual(replies[2].group_key, "B")
        self.assertEqual(replies[2].group_level, 0)
        self.assertIsNone(replies[2].drawables)

        # B leaf
        self.assertIsNone(replies[3].group_key)
        self.assertIsNone(replies[3].group_level)
        self.assertEqual(
            [d.name for d in replies[3].drawables],
            ["d3"],
        )
