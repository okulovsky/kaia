from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from .annotation_cache import IAnnotationCache
from .....common import ICacheEntity

import gradio as gr

TCache = TypeVar('TCache', bound=IAnnotationCache)

class IAnnotator(Generic[TCache], ABC):
    @property
    def cache(self) -> TCache:
        if not hasattr(self, '_cache'):
            raise AttributeError("Annotator has not been initialized")
        return self._cache

    def run(self, cache: TCache):
        self._cache = cache


    @abstractmethod
    def mock_annotation(self, cache: TCache):
        ...


class IGradioAnnotator(Generic[TCache], IAnnotator[TCache]):
    @abstractmethod
    def create_interface(self) -> gr.Blocks:
        ...

    def run(self, cache: TCache):
        super().run(cache)
        interface = self.create_interface()
        interface.launch(show_error=True)

