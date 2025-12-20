from .interfaces import IDrawable
from dataclasses import dataclass
from .selector import Selector

@dataclass
class Table:
    rows: list[list[IDrawable|None]]

@dataclass
class Orderer:
    column_count: int|None = None
    column_selector: Selector|None = None
    row_selector: Selector|None = None

    def __post_init__(self):
        if self.column_count is not None and self.row_selector is not None:
            raise ValueError('Cannot specify both column_count and row_selector')
        if self.row_selector is not None and self.column_selector is None:
            raise ValueError('If row selector is specified, column_selector must be specified')

    def _build_matrix(self, drawables: list[IDrawable]) -> Table:
        if self.column_selector is None or self.row_selector is None:
            raise ValueError('Must specify column_count and row_selector')
        rows = set()
        columns = set()
        for drawable in drawables:
            rows.add(self.row_selector(drawable))
            columns.add(self.column_selector(drawable))
        row_to_index = {row:i for i, row in enumerate(sorted(rows))}
        column_to_index = {column:i for i, column in enumerate(sorted(columns))}

        matrix = [[None for _ in columns] for _ in rows]
        for drawable in drawables:
            matrix[row_to_index[self.row_selector(drawable)]][column_to_index[self.column_selector(drawable)]] = drawable

        return Table(matrix)

    def _build_ordered(self, drawables: list[IDrawable]) -> Table:
        if self.column_selector is not None:
            drawables = sorted(drawables, key=lambda drawable: self.column_selector(drawable))
        result = []
        buffer = []
        for element in drawables:
            buffer.append(element)
            if self.column_count is not None and len(buffer) >= self.column_count:
                result.append(buffer)
                buffer = []
        if len(buffer) > 0:
            result.append(buffer)
        return Table(result)



    def build_table(self, drawables: list[IDrawable]) -> Table:
        if self.column_selector is not None and self.row_selector is not None:
            return self._build_matrix(drawables)
        return self._build_ordered(drawables)



