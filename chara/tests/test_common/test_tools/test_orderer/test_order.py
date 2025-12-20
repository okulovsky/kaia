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



class TestOrdererBuildOrdered(unittest.TestCase):
    def setUp(self):
        self.drawables = [
            DummyDrawable(row=0, col=3, name="d0"),
            DummyDrawable(row=0, col=1, name="d1"),
            DummyDrawable(row=0, col=4, name="d2"),
            DummyDrawable(row=0, col=2, name="d3"),
            DummyDrawable(row=0, col=0, name="d4"),
        ]
        self.col_selector = Selector(lambda d: d.col)

    def test_build_table_single_row_when_no_column_count(self):
        orderer = Orderer()
        table = orderer.build_table(self.drawables)

        # With no column_count, _build_ordered should put all into a single row
        self.assertEqual(len(table.rows), 1)
        self.assertEqual(table.rows[0], self.drawables)

    def test_build_table_chunked_by_column_count_without_sort(self):
        orderer = Orderer(column_count=2)
        table = orderer.build_table(self.drawables)

        # Column count = 2, 5 elements -> [[0,1], [2,3], [4]]
        self.assertEqual(len(table.rows), 3)
        self.assertEqual(table.rows[0], self.drawables[0:2])
        self.assertEqual(table.rows[1], self.drawables[2:4])
        self.assertEqual(table.rows[2], self.drawables[4:5])

    def test_build_table_sorted_then_chunked_when_column_selector_and_count(self):
        orderer = Orderer(column_count=2, column_selector=self.col_selector)
        table = orderer.build_table(self.drawables)

        # First, sort by col: col=0,1,2,3,4
        sorted_by_col = sorted(self.drawables, key=self.col_selector)

        # Then chunk by 2: [[0,1], [2,3], [4]]
        self.assertEqual(len(table.rows), 3)
        self.assertEqual(table.rows[0], sorted_by_col[0:2])
        self.assertEqual(table.rows[1], sorted_by_col[2:4])
        self.assertEqual(table.rows[2], sorted_by_col[4:5])

