from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterable, TypeVar, TYPE_CHECKING

from brainbox.deciders import Ollama
from foundation_kaia.prompters import AddressLike

from .illm import ILLM
from .steps import *

if TYPE_CHECKING:
    from .llm_request import LLMRequest
    from .llm_setup import LLMSetup

TCase = TypeVar('TCase')
TResult = TypeVar('TResult')
T = TypeVar('T')


class ILLMBuilder(ILLM[TCase, TResult]):
    """Fluent, append-only interface over the steps of a request.

    Every method below is expressed through `append`, so the two implementations only
    have to decide what appending and terminating mean.
    """

    @abstractmethod
    def append(self, step: LLMRequestStep) -> ILLMBuilder:
        pass

    @abstractmethod
    def to_request(self) -> LLMRequest[TCase, TResult]:
        pass

    def case_type(self, case_type: type[T]) -> ILLMBuilder[T, TResult]:
        return self.append(CaseTypization(case_type))

    def result_type(self, result_type: type[T], example: Any = None) -> ILLMBuilder[TCase, T]:
        return self.append(ResultTypization(result_type, example))

    def template(self,
                 file: Path|str,
                 additional_folders: Iterable[Path] = (),
                 main_field: str = 'case'
                 ) -> ILLMBuilder[TCase, TResult]:
        return self.append(JinjaTemplate(file, additional_folders, main_field))

    def custom_prompt(self, prompt: Callable[[TCase], str]) -> ILLMBuilder[TCase, TResult]:
        return self.append(CustomPrompt(prompt))

    def system_prompt(self, system_prompt: str) -> ILLMBuilder[TCase, TResult]:
        return self.append(SystemPrompt(system_prompt))

    def options(self, options: Ollama.Options|None = None, **kwargs) -> ILLMBuilder[TCase, TResult]:
        return self.append(Options(options, **kwargs))

    def image(self, image_address: AddressLike) -> ILLMBuilder[TCase, TResult]:
        return self.append(Image(image_address))

    def questionnaire(self, questions, intro: str|Callable[[TCase], str]|None = None) -> ILLMBuilder[TCase, TResult]:
        return self.append(Questionnaire(questions, intro))

    def parse(self,
              parser: Callable[[TCase, str], Any]|None = None,
              divider: Callable[[str], list]|None = None
              ) -> ILLMBuilder[TCase, TResult]:
        return self.append(CustomParse(parser, divider))

    def assign(self, address: AddressLike) -> ILLMBuilder[TCase, TResult]:
        return self.append(Assign(address))

    def entities(self, **kwargs) -> ILLMBuilder[TCase, TResult]:
        return self.append(TemplateEntities(**kwargs))

    def derived_case(self, factory: Callable[[TCase], Any], main_field: str = 'case') -> ILLMBuilder[TCase, TResult]:
        return self.append(DerivedCase(factory, main_field))


class LLMRequestBuilder(ILLMBuilder[TCase, TResult]):
    def __init__(self, setup: LLMSetup, steps: tuple[LLMRequestStep,...] = ()):
        self._setup = setup
        self.steps = steps

    @property
    def setup(self) -> LLMSetup:
        return self._setup

    def append(self, step: LLMRequestStep) -> LLMRequestBuilder[TCase, TResult]:
        return LLMRequestBuilder(self._setup, self.steps+(step,))

    def to_request(self) -> LLMRequest[TCase, TResult]:
        from .llm_request import LLMRequest
        return LLMRequest(self._setup, self.steps)

    def default(self) -> ILLMBuilder[TCase, TResult]:
        return NoOpBuilder(self.to_request())


class NoOpBuilder(ILLMBuilder[TCase, TResult]):
    """Swallows every appended step and yields the request it was created from.

    This is what makes `x.default().template(...).to_request()` mean "these are the
    defaults, unless `x` is already a configured request".
    """

    def __init__(self, origin: LLMRequest[TCase, TResult]):
        self.origin = origin

    @property
    def setup(self) -> LLMSetup:
        return self.origin.setup

    def append(self, step: LLMRequestStep) -> NoOpBuilder[TCase, TResult]:
        return self

    def to_request(self) -> LLMRequest[TCase, TResult]:
        return self.origin

    def default(self) -> ILLMBuilder[TCase, TResult]:
        return self
