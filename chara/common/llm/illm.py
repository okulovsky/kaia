from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .builder import ILLMBuilder
    from .llm_setup import LLMSetup

TCase = TypeVar('TCase')
TResult = TypeVar('TResult')


class ILLM(Generic[TCase, TResult], ABC):
    """What a pipeline accepts when it wants to talk to an LLM.

    A setup, a builder or an already configured request are all one of these, so a
    pipeline takes an `ILLM`, writes its defaults through `default()`, and gets back
    either the chain it just built or the caller's request untouched.
    """

    @abstractmethod
    def default(self) -> ILLMBuilder[TCase, TResult]:
        pass

    @property
    @abstractmethod
    def setup(self) -> LLMSetup:
        """The engine and model to use, for building sibling requests off the same pair."""
