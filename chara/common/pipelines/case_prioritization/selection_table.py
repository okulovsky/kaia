from dataclasses import dataclass
import math


@dataclass
class SelectionTableRow:
    label: str
    fingerprints: int = 0
    pool: int = 0
    selected: int = 0
    after_total: float = 0.0

    @property
    def after(self) -> float|None:
        if self.fingerprints == 0:
            return None
        return self.after_total / self.fingerprints


def _bucket_index(level: int) -> int:
    if level <= 2:
        return level
    return (level - 1).bit_length() + 1


def _bucket_label(index: int) -> str:
    if index <= 2:
        return str(index)
    power = index - 1
    return f'{2**(power - 1) + 1}-{2**power}'


def build_selection_table(rows: list[tuple[float, float, int, int]]) -> list[SelectionTableRow]:
    """Each input row is (level, level_after, pool, selected) of one fingerprint. The level before
    the selection is floored and bucketed as 0, 1, 2, 3-4, 5-8, 9-16, ...; all the buckets up to
    the largest are returned, empty ones included. `after` is the average level_after of the bucket."""
    if len(rows) == 0:
        return []
    indices = [_bucket_index(int(math.floor(level))) for level, _, _, _ in rows]
    table = [SelectionTableRow(_bucket_label(i)) for i in range(max(indices) + 1)]
    for index, (_, after, pool, selected) in zip(indices, rows):
        table[index].fingerprints += 1
        table[index].pool += pool
        table[index].selected += selected
        table[index].after_total += after
    return table


def format_selection_table(level_name: str, table: list[SelectionTableRow]) -> str:
    headers = (level_name, 'fingerprints', 'pool', 'selected', 'after')
    lines = [headers] + [
        (r.label, str(r.fingerprints), str(r.pool), str(r.selected), '-' if r.after is None else f'{r.after:.1f}')
        for r in table
    ]
    widths = [max(len(line[i]) for line in lines) for i in range(len(headers))]
    return '\n'.join('  ' + '  '.join(cell.rjust(width) for cell, width in zip(line, widths)) for line in lines)
