from dataclasses import dataclass
from typing import Any, Callable, Iterable
from ..core import IDrawable
from .drawer_element import DrawerElement
from .selector import Selector
from .table import TablePresenter
from .tiling import Tiling
from .util import normalize_selector_keys

@dataclass
class OutputElement:
    header_key: Any = None
    header_level: int = None
    elements: list[DrawerElement]|None = None


@dataclass
class Drawer:
    def __init__(self,
                 data: Iterable,
                 item_to_drawable: Callable[[Any], IDrawable]|None = None,
                 item_to_metadata: Callable[[Any], Any]|None = None,
                 ):
        collection = []
        for item in data:
            if item_to_drawable is not None:
                drawable = item_to_drawable(item)
            elif isinstance(item, IDrawable):
                drawable = item
            else:
                raise ValueError(f"Item {item} is not IDrawable and item_to_drawable is not set")

            if item_to_metadata is not None:
                metadata = item_to_metadata(item)
            elif isinstance(item, IDrawable):
                metadata = item.metadata
            else:
                metadata = item

            collection.append(DrawerElement(drawable, metadata))

        self.collection = tuple(collection)
        self._groups: tuple[Selector,...] = ()
        self._presenter = None


    def group(self, selector: Any):
        self._groups = self._groups + (Selector(selector),)
        return self

    def tiles(self,
               column_selector_or_column_count: str|Callable|int|None = None,
               row_selector: str|Callable|None = None,
               *metadata_to_print: Any) -> 'Drawer':
        if row_selector is not None:
            if isinstance(column_selector_or_column_count, int):
                raise ValueError("If second selector is set, first_selector cannot be int")
            self._presenter = Tiling(None, Selector(column_selector_or_column_count), Selector(row_selector))
        else:
            if isinstance(column_selector_or_column_count, int):
                self._presenter = Tiling(column_selector_or_column_count)
            elif column_selector_or_column_count is not None:
                self._presenter = Tiling(None, Selector(column_selector_or_column_count), None)
            else:
                self._presenter = Tiling()
        self._presenter.metadata_to_print = tuple(Selector(e) for e in metadata_to_print)
        return self

    def table(self, *columns) -> 'Drawer':
        self._presenter = TablePresenter(tuple(Selector(c) for c in columns))
        return self

    def _iterate_output(self, level: int, elements: list[DrawerElement]) -> Iterable[OutputElement]:
        if level < len(self._groups):
            key_to_elements = {}
            for element in elements:
                key = self._groups[level].get(element.metadata)
                if key not in key_to_elements:
                    key_to_elements[key] = []
                key_to_elements[key].append(element)
            key_to_elements = normalize_selector_keys(key_to_elements)
            for key in sorted(key_to_elements.keys()):
                yield OutputElement(key, level)
                yield from self._iterate_output(level+1, key_to_elements[key])
        else:
            yield OutputElement(elements=elements)


    def to_html(self):
        result = []
        for element in self._iterate_output(0, list(self.collection)):
            if element.header_key is not None:
                result.append(f'<h{element.header_level+1}>{element.header_key}</h{element.header_level+1}>')
            else:
                result.append(self._presenter.to_html(element.elements))
        return "\n".join(result)










