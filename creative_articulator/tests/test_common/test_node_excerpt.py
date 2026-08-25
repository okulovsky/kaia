import unittest

from creative_articulator.common import Node
from creative_articulator.common.node import LinearizedNode


class TestNodeExcerpt(unittest.TestCase):
    def setUp(self):
        self.root = Node()
        self.a = self.root.append(Node())
        self.b = self.root.append(Node())
        self.c = self.root.append(Node())

        self.b1 = self.b.append(Node())
        self.b2 = self.b.append(Node())
        self.b3 = self.b.append(Node())

        self.names = {
            self.root: 'root',
            self.a: 'a',
            self.b: 'b',
            self.c: 'c',
            self.b1: 'b1',
            self.b2: 'b2',
            self.b3: 'b3',
        }

    def _view(self, items: list[LinearizedNode]) -> list[tuple[str, int]]:
        return [(self.names[item.node], item.level) for item in items]

    def test_left_excerpt_default(self):
        result = list(self.b2.left_excerpt())
        self.assertEqual(self._view(result), [
            ('root', -2), ('a', -1), ('b', -1), ('b1', 0), ('b2', 0),
        ])

    def test_left_excerpt_exclude_self(self):
        result = list(self.b2.left_excerpt(include_self=False))
        self.assertEqual(self._view(result), [
            ('root', -2), ('a', -1), ('b', -1), ('b1', 0),
        ])

    def test_left_excerpt_exclude_parents(self):
        result = list(self.b2.left_excerpt(include_parents=False))
        self.assertEqual(self._view(result), [
            ('a', -1), ('b1', 0), ('b2', 0),
        ])

    def test_left_excerpt_exclude_self_and_parents(self):
        result = list(self.b2.left_excerpt(include_self=False, include_parents=False))
        self.assertEqual(self._view(result), [
            ('a', -1), ('b1', 0),
        ])

    def test_right_excerpt_default(self):
        result = list(self.b2.right_excerpt())
        self.assertEqual(self._view(result), [
            ('b2', 0), ('b3', 0), ('b', -1), ('c', -1), ('root', -2),
        ])

    def test_right_excerpt_exclude_self(self):
        result = list(self.b2.right_excerpt(include_self=False))
        self.assertEqual(self._view(result), [
            ('b3', 0), ('b', -1), ('c', -1), ('root', -2),
        ])

    def test_right_excerpt_exclude_parents(self):
        result = list(self.b2.right_excerpt(include_parents=False))
        self.assertEqual(self._view(result), [
            ('b2', 0), ('b3', 0), ('c', -1),
        ])

    def test_right_excerpt_exclude_self_and_parents(self):
        result = list(self.b2.right_excerpt(include_self=False, include_parents=False))
        self.assertEqual(self._view(result), [
            ('b3', 0), ('c', -1),
        ])

    def test_left_excerpt_leftmost_node_has_no_siblings_or_earlier_ancestors(self):
        result = list(self.a.left_excerpt())
        self.assertEqual(self._view(result), [
            ('root', -1), ('a', 0),
        ])

    def test_right_excerpt_rightmost_node_has_no_siblings(self):
        result = list(self.c.right_excerpt())
        self.assertEqual(self._view(result), [
            ('c', 0), ('root', -1),
        ])

    def test_root_left_excerpt_has_only_self(self):
        result = list(self.root.left_excerpt())
        self.assertEqual(self._view(result), [
            ('root', 0),
        ])

    def test_root_right_excerpt_has_only_self(self):
        result = list(self.root.right_excerpt())
        self.assertEqual(self._view(result), [
            ('root', 0),
        ])

    def test_root_excerpt_empty_when_self_excluded(self):
        self.assertEqual(list(self.root.left_excerpt(include_self=False)), [])
        self.assertEqual(list(self.root.right_excerpt(include_self=False)), [])


if __name__ == '__main__':
    unittest.main()
