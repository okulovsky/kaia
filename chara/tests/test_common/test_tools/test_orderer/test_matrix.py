import unittest
from chara.common.tools.core.orderer import Orderer, Table, Selector, IDrawable
from dataclasses import dataclass


@dataclass
class DummyDrawable:
    """
    Minimal stub used for testing. It does NOT need to inherit from IDrawable
    because the implementation only uses the attributes accessed via selectors.
    """
    row: int
    col: int
    name: str


class TestOrdererBuildMatrix(unittest.TestCase):
    def setUp(self):
        # Three elements, two rows (0, 1) and two columns (0, 1)
        self.drawables = [
            DummyDrawable(row=0, col=0, name="a"),
            DummyDrawable(row=0, col=1, name="b"),
            DummyDrawable(row=1, col=0, name="c"),
        ]
        self.row_selector = Selector(lambda d: d.row)
        self.col_selector = Selector(lambda d: d.col)

    def test_build_table_matrix_shape_and_contents(self):
        orderer = Orderer(
            column_selector=self.col_selector,
            row_selector=self.row_selector,
        )

        table = orderer.build_table(self.drawables)
        self.assertIsInstance(table, Table)

        # Expect 2 rows
        self.assertEqual(len(table.rows), 2)
        # Expect 2 columns per row
        self.assertEqual(len(table.rows[0]), 2)
        self.assertEqual(len(table.rows[1]), 2)

        self.assertIs(table.rows[0][0], self.drawables[0])  # (row=0, col=0)
        self.assertIs(table.rows[0][1], self.drawables[1])  # (row=0, col=1)
        self.assertIs(table.rows[1][0], self.drawables[2])  # (row=1, col=0)
        self.assertIsNone(table.rows[1][1])                  # (row=1, col=1) missing

    def test_build_table_matrix_sorts_rows_and_columns(self):
        # Scramble ordering of drawables and coordinates
        drawables = [
            DummyDrawable(row=2, col=3, name="d"),
            DummyDrawable(row=0, col=1, name="a"),
            DummyDrawable(row=2, col=1, name="b"),
            DummyDrawable(row=0, col=3, name="c"),
        ]

        orderer = Orderer(
            column_selector=self.col_selector,
            row_selector=self.row_selector,
        )

        table = orderer.build_table(drawables)

        # Sorted rows: [0, 2]
        # Sorted columns: [1, 3]
        # Expected matrix:
        # row=0: col=1 -> "a", col=3 -> "c"
        # row=2: col=1 -> "b", col=3 -> "d"
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(len(table.rows[0]), 2)
        self.assertEqual(len(table.rows[1]), 2)

        self.assertEqual(table.rows[0][0].name, "a")
        self.assertEqual(table.rows[0][1].name, "c")
        self.assertEqual(table.rows[1][0].name, "b")
        self.assertEqual(table.rows[1][1].name, "d")

    def test_build_matrix_raises_if_selectors_missing(self):
        # Directly test the private method to ensure it enforces its precondition
        orderer = Orderer()
        with self.assertRaises(ValueError):
            orderer._build_matrix(self.drawables)
