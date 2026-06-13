from dataclasses import dataclass
from .selector import Selector
from .drawer_element import DrawerElement
from .util import normalize_selector_keys
from typing import Iterable

@dataclass
class TilingTable:
    table: list[list[list[DrawerElement]]]
    columns: list | None
    rows: list | None


@dataclass
class Tiling:
    column_count: int | None = None
    column_selector: Selector | None = None
    row_selector: Selector | None = None
    metadata_to_print: list[Selector]|None = None

    def __post_init__(self):
        if self.row_selector is not None and self.column_selector is None:
            raise ValueError("If row_selector is not None, column_selector must be set")
        if self.column_count is not None and self.column_selector is not None:
            raise ValueError("column_count and column_selector cannot be both set")

    def _no_selector_tiling(self, elements: Iterable[DrawerElement]) -> TilingTable:
        rows = []
        current_row = []
        rows.append(current_row)
        for element in elements:
            if self.column_count is not None and len(current_row) == self.column_count:
                current_row = []
                rows.append(current_row)
            current_row.append([element])
        return TilingTable(rows, None, None)

    def _no_row_selector_tiling(self, elements: Iterable[DrawerElement]) -> TilingTable:
        column_to_elements = {}
        for element in elements:
            key = self.column_selector.get(element.metadata)
            if key not in column_to_elements:
                column_to_elements[key] = []
            column_to_elements[key].append(element)
        column_to_elements = normalize_selector_keys(column_to_elements)
        rows_count = max(len(e) for e in column_to_elements.values())
        keys = list(sorted(column_to_elements.keys()))

        rows = []
        for i in range(rows_count):
            current_row = []
            for key in keys:
                if i < len(column_to_elements[key]):
                    current_row.append([column_to_elements[key][i]])
                else:
                    current_row.append([])
            rows.append(current_row)

        return TilingTable(rows, keys, None)

    def _both_selectors_tiling(self, elements: Iterable[DrawerElement]) -> TilingTable:
        row_to_column_to_element = {}
        for element in elements:
            row_key = self.row_selector.get(element.metadata)
            if row_key not in row_to_column_to_element:
                row_to_column_to_element[row_key] = {}
            column_key = self.column_selector.get(element.metadata)
            if column_key not in row_to_column_to_element[row_key]:
                row_to_column_to_element[row_key][column_key] = []
            row_to_column_to_element[row_key][column_key].append(element)

        row_to_column_to_element = normalize_selector_keys(row_to_column_to_element)
        for row_key in row_to_column_to_element:
            row_to_column_to_element[row_key] = normalize_selector_keys(row_to_column_to_element[row_key])
        all_columns = set(col for inner in row_to_column_to_element.values() for col in inner)

        rows_keys = list(sorted(row_to_column_to_element.keys()))
        column_keys = list(sorted(all_columns))

        rows = []
        for row_key in rows_keys:
            current_row = []
            for column_key in column_keys:
                if column_key not in row_to_column_to_element[row_key]:
                    current_row.append([])
                else:
                    current_row.append(row_to_column_to_element[row_key][column_key])
            rows.append(current_row)

        return TilingTable(rows, column_keys, rows_keys)

    def _get_table(self, elements: Iterable[DrawerElement]) -> TilingTable:
        if self.row_selector is None:
            if self.column_selector is None:
                return self._no_selector_tiling(elements)
            else:
                return self._no_row_selector_tiling(elements)
        else:
            return self._both_selectors_tiling(elements)

    def to_html(self, elements: Iterable[DrawerElement]) -> str:
        table = self._get_table(elements)

        parts = ['<table style="border: none; border-collapse: collapse;">']

        if table.columns is not None:
            parts.append('<thead><tr>')
            if table.rows is not None:
                parts.append('<th></th>')
            for col in table.columns:
                parts.append(f'<th>{col}</th>')
            parts.append('</tr></thead>')

        parts.append('<tbody>')
        for row_idx, row in enumerate(table.table):
            parts.append('<tr>')
            if table.rows is not None:
                parts.append(f'<td>{table.rows[row_idx]}</td>')
            for cell in row:
                cell_parts = []
                for element in cell:
                    elem_html = element.drawable.to_html()
                    if self.metadata_to_print:
                        meta_values = [str(s.get(element.metadata)) for s in self.metadata_to_print]
                        cell_parts.append('<br>'.join([elem_html] + meta_values))
                    else:
                        cell_parts.append(elem_html)
                parts.append(f'<td>{"<br>".join(cell_parts)}</td>')
            parts.append('</tr>')
        parts.append('</tbody></table>')

        return '\n'.join(parts)





