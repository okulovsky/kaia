from dataclasses import dataclass

from .interfaces import IDrawable
from .selector import Selector
from typing import Any
import ipywidgets as W

@dataclass
class TableRow:
    drawable: IDrawable
    values: list[Any]

@dataclass
class Table:
    columns: list[str]
    rows: list[TableRow]

    def to_widget(self,
        *,
        drawable_header: str = "",
        gap: str = "6px 10px",
        align: str = "center",
        value_width: str|None = None,  # e.g. "140px"
        drawable_width: str|None = None,  # e.g. "220px"
        ):
        """
        Render Table into an ipywidgets GridBox.

        Columns:
          [drawable_header] + table.columns

        Each row:
          drawable.to_widget() + Labels for primitive values
        """
        n_value_cols = len(self.columns)
        n_cols = 1 + n_value_cols

        # Build grid-template-columns
        col_sizes: list[str] = []
        col_sizes.append(drawable_width or "max-content")
        col_sizes.extend([value_width or "max-content"] * n_value_cols)

        # Small helper to make header cells
        def header_cell(text: str) -> W.HTML:
            return W.HTML(f"<b>{text}</b>", layout=W.Layout(align_self=align))

        # Small helper to make value cells
        def value_cell(v: Any) -> W.Label:
            s = "" if v is None else str(v)
            return W.Label(s, layout=W.Layout(align_self=align))

        # Build children in row-major order
        children: list[W.Widget] = []

        # Header row
        children.append(header_cell(drawable_header))
        for c in self.columns:
            children.append(header_cell(c))

        # Data rows
        for r in self.rows:
            children.append(r.drawable.to_widget())
            # If a row is shorter/longer than columns, normalize to fit the grid
            vals = (list(r.values) + [None] * n_value_cols)[:n_value_cols]
            for v in vals:
                children.append(value_cell(v))

        grid = W.GridBox(
            children=children,
            layout=W.Layout(
                display="grid",
                grid_template_columns=" ".join(col_sizes),
                grid_auto_rows="max-content",
                grid_gap=gap,
                align_items="center",
            ),
        )
        return grid



@dataclass
class TableView:
    head: int | None = None
    order_by: Selector | None = None
    ascending: bool = True
    exclude: list[str] | None = None
    include: list[str] | None = None

    def build_table(self, drawable: list[IDrawable]) -> Table:
        if self.order_by is not None:
            drawable = list(sorted(drawable, key=self.order_by, reverse=not self.ascending))
        if self.head is not None:
            drawable = drawable[:self.head]


        if self.include is not None:
            columns = list(self.include)
        else:
            columns_set = set()
            columns = []
            for d in drawable:
                for key in d.metadata:
                    if key not in columns_set:
                        columns_set.add(key)
                        columns.append(key)

        exclude = set(self.exclude) if self.exclude is not None else set()
        columns = [c for c in columns if c not in exclude]

        rows = []
        for d in drawable:
            meta = [d.metadata.get(c, None) for c in columns]
            rows.append(TableRow(d, meta))

        return Table(columns, rows)







