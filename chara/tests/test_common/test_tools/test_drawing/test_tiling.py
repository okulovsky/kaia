import unittest
from chara.common.tools.drawing.core import IDrawable
from chara.common.tools.drawing.drawer.tiling import Tiling
from chara.common.tools.drawing.drawer.selector import Selector
from chara.common.tools.drawing.drawer.drawer_element import DrawerElement


class E(IDrawable):
    def __init__(self, html: str):
        self.html = html

    def to_html(self) -> str:
        return self.html


def el(html, **meta):
    return DrawerElement(E(html), meta)


col = Selector('col')
row = Selector('row')


def html_at(table, r, c, i=0):
    return table.table[r][c][i].drawable.to_html()


class BothSelectorsTilingTestCase(unittest.TestCase):

    def test_full_grid_shape(self):
        elements = [
            el('AX', row='A', col='X'),
            el('AY', row='A', col='Y'),
            el('BX', row='B', col='X'),
            el('BY', row='B', col='Y'),
        ]
        table = Tiling(column_selector=col, row_selector=row)._get_table(elements)
        self.assertEqual(2, len(table.table))
        self.assertEqual(2, len(table.table[0]))

    def test_full_grid_headers(self):
        elements = [
            el('AX', row='A', col='X'),
            el('BY', row='B', col='Y'),
        ]
        table = Tiling(column_selector=col, row_selector=row)._get_table(elements)
        self.assertEqual(['X', 'Y'], table.columns)
        self.assertEqual(['A', 'B'], table.rows)

    def test_full_grid_cell_contents(self):
        elements = [
            el('AX', row='A', col='X'),
            el('AY', row='A', col='Y'),
            el('BX', row='B', col='X'),
            el('BY', row='B', col='Y'),
        ]
        table = Tiling(column_selector=col, row_selector=row)._get_table(elements)
        self.assertEqual('AX', html_at(table, 0, 0))
        self.assertEqual('AY', html_at(table, 0, 1))
        self.assertEqual('BX', html_at(table, 1, 0))
        self.assertEqual('BY', html_at(table, 1, 1))

    def test_missing_cell_is_empty_list(self):
        elements = [
            el('AX', row='A', col='X'),
            el('AY', row='A', col='Y'),
            el('BX', row='B', col='X'),
        ]
        table = Tiling(column_selector=col, row_selector=row)._get_table(elements)
        self.assertEqual([], table.table[1][1])

    def test_multiple_elements_in_cell(self):
        elements = [
            el('AX1', row='A', col='X'),
            el('AX2', row='A', col='X'),
            el('AY', row='A', col='Y'),
        ]
        table = Tiling(column_selector=col, row_selector=row)._get_table(elements)
        self.assertEqual(2, len(table.table[0][0]))
        self.assertEqual('AX1', html_at(table, 0, 0, 0))
        self.assertEqual('AX2', html_at(table, 0, 0, 1))

    def test_keys_are_sorted(self):
        elements = [
            el('BX', row='B', col='X'),
            el('AY', row='A', col='Y'),
            el('AX', row='A', col='X'),
            el('BY', row='B', col='Y'),
        ]
        table = Tiling(column_selector=col, row_selector=row)._get_table(elements)
        self.assertEqual(['X', 'Y'], table.columns)
        self.assertEqual(['A', 'B'], table.rows)
        self.assertEqual('AX', html_at(table, 0, 0))
        self.assertEqual('BY', html_at(table, 1, 1))


class ColumnSelectorOnlyTilingTestCase(unittest.TestCase):

    def test_equal_columns_one_row(self):
        elements = [el('X1', col='X'), el('Y1', col='Y')]
        table = Tiling(column_selector=col)._get_table(elements)
        self.assertEqual(['X', 'Y'], table.columns)
        self.assertIsNone(table.rows)
        self.assertEqual(1, len(table.table))
        self.assertEqual('X1', html_at(table, 0, 0))
        self.assertEqual('Y1', html_at(table, 0, 1))

    def test_uneven_columns_row_count(self):
        elements = [el('X1', col='X'), el('X2', col='X'), el('Y1', col='Y')]
        table = Tiling(column_selector=col)._get_table(elements)
        self.assertEqual(2, len(table.table))

    def test_uneven_columns_short_column_has_empty_cell(self):
        elements = [el('X1', col='X'), el('X2', col='X'), el('Y1', col='Y')]
        table = Tiling(column_selector=col)._get_table(elements)
        self.assertEqual('X1', html_at(table, 0, 0))
        self.assertEqual('Y1', html_at(table, 0, 1))
        self.assertEqual('X2', html_at(table, 1, 0))
        self.assertEqual([], table.table[1][1])


class NoSelectorTilingTestCase(unittest.TestCase):

    def test_all_elements_in_single_row(self):
        elements = [el('A'), el('B'), el('C')]
        table = Tiling()._get_table(elements)
        self.assertIsNone(table.columns)
        self.assertIsNone(table.rows)
        self.assertEqual(1, len(table.table))
        self.assertEqual(3, len(table.table[0]))

    def test_each_cell_is_single_element_list(self):
        elements = [el('A'), el('B')]
        table = Tiling()._get_table(elements)
        self.assertEqual(1, len(table.table[0][0]))
        self.assertEqual('A', html_at(table, 0, 0))
        self.assertEqual('B', html_at(table, 0, 1))

    def test_column_count_wraps_into_rows(self):
        elements = [el('A'), el('B'), el('C'), el('D'), el('E')]
        table = Tiling(column_count=2)._get_table(elements)
        self.assertEqual(3, len(table.table))
        self.assertEqual(2, len(table.table[0]))
        self.assertEqual(2, len(table.table[1]))
        self.assertEqual(1, len(table.table[2]))

    def test_column_count_cell_contents(self):
        elements = [el('A'), el('B'), el('C'), el('D')]
        table = Tiling(column_count=2)._get_table(elements)
        self.assertEqual('A', html_at(table, 0, 0))
        self.assertEqual('B', html_at(table, 0, 1))
        self.assertEqual('C', html_at(table, 1, 0))
        self.assertEqual('D', html_at(table, 1, 1))


class TilingValidationTestCase(unittest.TestCase):

    def test_row_selector_without_column_raises(self):
        with self.assertRaises(ValueError):
            Tiling(row_selector=row)

    def test_column_count_and_column_selector_raises(self):
        with self.assertRaises(ValueError):
            Tiling(column_count=3, column_selector=col)
