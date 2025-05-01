from typing import *
from dataclasses import dataclass
from abc import ABC, abstractmethod
from yo_fluq import Query, fluq
import ipywidgets

T = TypeVar('T')

class Drawer(ABC, Generic[T]):
    @dataclass
    class Item:
        source: Any
        img: T

    def __init__(self, sources: Iterable):
        self._images = list(sources)
        self._retriever: Optional[Callable[[Any], T]] = None
        self._captioner: Optional[Callable[[T], str]] = None

    def retrieve(self, function: Callable[[Any], T]) -> 'Drawer':
        self._retriever = function
        return self

    def caption(self, function: Callable[[Any], str]) -> 'Drawer':
        self._captioner = function
        return self


    @abstractmethod
    def _to_one_widget(self, objects: Iterable[Tuple[T, str|None]]):
        pass

    def _retrieve_postprocess(self, s):
        return s


    def _draw_internal(self, images: list['Drawer.Item'], selectors: list, level):
        if len(selectors) == 0:
            captioner = self._captioner
            if captioner is None:
                captioner = lambda _:''
            return self._to_one_widget((item.img, captioner(item.source)) for item in images)

        selector = lambda z: selectors[0](z.source)
        captioner = (lambda z: self._captioner(z.source)) if self._captioner is not None else selector
        if len(selectors) == 1:
            return (
                Query
                .en(images)
                .order_by(selector)
                .select(lambda z: (z.img,captioner(z)))
                .feed(list, self._to_one_widget)
            )
        rows = []
        for group in Query.en(images).group_by(selector).order_by(lambda z: z.key):
            rows.append(ipywidgets.HTML(f'<h{level}>{group.key}</h{level}>'))
            rows.append(self._draw_internal(group.value, selectors[1:], level+1))
        return ipywidgets.VBox(rows)

    def draw(self, *selectors):
        items = []
        query = Query.en(self._images).feed(fluq.with_progress_bar())
        for src in query:
            if self._retriever is not None:
                items.append(Drawer.Item(src, self._retrieve_postprocess(self._retriever(src))))
            else:
                items.append(Drawer.Item(src, self._retrieve_postprocess(src)))
        return self._draw_internal(items, list(selectors), 1)
