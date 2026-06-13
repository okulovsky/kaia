from dataclasses import dataclass
from .selector import Selector
from .drawer_element import DrawerElement
from .util import normalize_values
from typing import Iterable


@dataclass
class Row:
    element: DrawerElement
    keys: tuple


@dataclass
class TablePresenter:
    columns: tuple[Selector, ...]

    def _column_header(self, selector: Selector) -> str:
        if selector.address is not None:
            return str(selector.address)
        return ''

    def _build_rows(self, elements: Iterable[DrawerElement]) -> list[Row]:
        elements = list(elements)
        if not elements:
            return []

        raw_columns = [
            [selector.get(elem.metadata) for elem in elements]
            for selector in self.columns
        ]
        normalized_columns = [normalize_values(col) for col in raw_columns]

        return [
            Row(
                element=elem,
                keys=tuple(normalized_columns[c][i] for c in range(len(self.columns)))
            )
            for i, elem in enumerate(elements)
        ]

    def to_html(self, elements: Iterable[DrawerElement]) -> str:
        rows = sorted(self._build_rows(elements), key=lambda r: r.keys)

        parts = ['<table style="border: none; border-collapse: collapse;">']

        parts.append('<thead><tr>')
        parts.append('<th></th>')
        for selector in self.columns:
            parts.append(f'<th>{self._column_header(selector)}</th>')
        parts.append('</tr></thead>')

        parts.append('<tbody>')
        for row in rows:
            parts.append('<tr>')
            parts.append(f'<td>{row.element.drawable.to_html()}</td>')
            for key in row.keys:
                parts.append(f'<td>{key}</td>')
            parts.append('</tr>')
        parts.append('</tbody></table>')

        return '\n'.join(parts)
