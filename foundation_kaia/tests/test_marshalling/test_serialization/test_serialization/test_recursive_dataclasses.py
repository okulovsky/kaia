from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from unittest import TestCase
from foundation_kaia.marshalling import Serializer


@dataclass
class TreeNode:
    value: int
    left: Optional[TreeNode] = None
    right: Optional[TreeNode] = None


class TestRecursiveDataclasses(TestCase):
    def test_tree_round_trip(self):
        tree = TreeNode(
            value=1,
            left=TreeNode(value=2, left=TreeNode(value=4), right=TreeNode(value=5)),
            right=TreeNode(value=3),
        )
        s = Serializer.parse(TreeNode)
        ctx = Serializer.Context()
        restored = s.from_json(s.to_json(tree, ctx), ctx)
        self.assertEqual(tree, restored)

    def test_circular_reference_raises(self):
        node = TreeNode(value=1)
        node.left = node
        s = Serializer.parse(TreeNode)
        with self.assertRaises(RecursionError):
            s.to_json(node, Serializer.Context())
