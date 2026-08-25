from __future__ import annotations

from typing import TYPE_CHECKING

from .engines import ILLMEngine
from .illm import ILLM

if TYPE_CHECKING:
    from .builder import LLMRequestBuilder


class LLMSetup(ILLM):
    """Everything a request needs beside its steps: where to send the prompt, and as which model."""

    def __init__(self, engine: ILLMEngine, model: str):
        self.engine = engine
        self.model = model

    @property
    def setup(self) -> LLMSetup:
        return self

    def default(self) -> LLMRequestBuilder:
        from .builder import LLMRequestBuilder
        return LLMRequestBuilder(self, ())

    def debug(self, flag: bool = True) -> LLMSetup:
        return LLMSetup(self.engine.with_debug(flag), self.model)

    def __eq__(self, other):
        return isinstance(other, LLMSetup) and self.engine == other.engine and self.model == other.model

    def __repr__(self):
        return f'LLMSetup({self.engine!r}, {self.model!r})'
