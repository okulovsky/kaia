from typing import *
from .template_metadata import ParaphraseInfo

T = TypeVar("T")

class Paraphrase(Generic[T]):
    def __init__(self, template: T):
        self._template = template
        self._story = False

    @property
    def story(self) -> 'Paraphrase[T]':
        self._story = True
        return self

    def __call__(self, narration: None|str = None) -> T:
        return self._template.meta.set(paraphrase=ParaphraseInfo(ParaphraseInfo.Type.Instead, narration, self._story))

    def after(self, narration: None|str = None) -> T:
        return self._template.meta.set(paraphrase=ParaphraseInfo(ParaphraseInfo.Type.After, narration, self._story))



