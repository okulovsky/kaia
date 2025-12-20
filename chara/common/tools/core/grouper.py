from .selector import Selector
from .interfaces import IDrawable
from dataclasses import dataclass
from typing import Any, Iterable

@dataclass
class Reply:
    group_key: Any
    group_level: int|None
    drawables: list[IDrawable]|None

@dataclass
class Grouper:
    selectors: list[Selector]

    def _group(self, drawables: list[IDrawable], group_index: int) -> Iterable[Reply]:
        if group_index >= len(self.selectors):
            yield Reply(None, None, drawables)
            return
        groups = {}
        for drawable in drawables:
            key = self.selectors[group_index](drawable)
            if key not in groups:
                groups[key] = []
            groups[key].append(drawable)

        for key in sorted(groups.keys()):
            yield Reply(key, group_index, None)
            yield from self._group(groups[key], group_index + 1)

    def group(self, drawables: list[IDrawable]) -> Iterable[Reply]:
        yield from self._group(drawables, 0)