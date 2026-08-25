from __future__ import annotations

from typing import TypeVar, Any, TYPE_CHECKING

from brainbox import BrainBox
from brainbox.deciders import Ollama

from .illm import ILLM
from .llm_request_applicator import LLMRequestApplicator
from .llm_setup import LLMSetup
from .engines import ILLMEngine, BrainBoxLLMEngine
from .steps import *
from ..pipelines import BrainBoxCasePipeline

if TYPE_CHECKING:
    from .builder import ILLMBuilder, LLMRequestBuilder

TCase = TypeVar('TCase')
TResult = TypeVar('TResult')
T = TypeVar('T')


class LLMRequest(ILLM[TCase, TResult]):
    """A setup plus a fixed chain of steps. Immutable: `edit()` is the only way to change it."""

    def __init__(self, setup: LLMSetup, steps: tuple[LLMRequestStep,...] = ()):
        self._setup = setup
        self.steps = steps

    @property
    def setup(self) -> LLMSetup:
        return self._setup

    @property
    def engine(self) -> ILLMEngine:
        return self._setup.engine

    @property
    def model(self) -> str:
        return self._setup.model

    def default(self) -> ILLMBuilder[TCase, TResult]:
        from .builder import NoOpBuilder
        return NoOpBuilder(self)

    def edit(self) -> LLMRequestBuilder[TCase, TResult]:
        from .builder import LLMRequestBuilder
        return LLMRequestBuilder(self._setup, self.steps)

    def _build_arguments(self, case: TCase) -> dict:
        template_entities = {}
        for step in self.steps:
            step.fill_template_entities(case, template_entities)

        arguments = {}
        options = None
        for step in self.steps:
            step.fill_arguments(case, template_entities, arguments)
            options = step.update_options(case, options)

        if arguments.get('prompt', None) is None:
            raise ValueError(
                f"No prompt was produced by the steps {[type(s).__name__ for s in self.steps]}. "
                f"A request needs a template, a custom prompt or a questionnaire."
            )
        arguments['options'] = options
        return arguments

    def build_prompt(self, case: TCase) -> str:
        return self._build_arguments(case)['prompt']

    def create_task(self, case: TCase) -> BrainBox.Task:
        return Ollama.new_task(parameter=self.model).question(**self._build_arguments(case))

    def postprocess_output(self, case: TCase, output: str) -> TResult:
        applicator = LLMRequestApplicator(self.steps)
        if applicator.divider is not None:
            raise ValueError("When outside of pipeline, divider must be None")
        return applicator.postprocess_output(case, output)

    def start_execution(self, case: TCase) -> Any:
        task = self.create_task(case)
        return self.engine.start(task)

    def join_execution(self, case: TCase, token: Any) -> TResult:
        output = self.engine.join(token)
        return self.postprocess_output(case, output)

    def execute(self, case: TCase) -> TResult:
        return self.join_execution(case, self.start_execution(case))

    def create_brainbox_pipeline(self) -> BrainBoxCasePipeline[TCase]:
        if not isinstance(self.engine, BrainBoxLLMEngine):
            raise ValueError(
                f"Pipelines run on BrainBox, but the engine is {type(self.engine).__name__}. "
                f"Use `execute` instead."
            )
        applicator = LLMRequestApplicator(self.steps)
        return BrainBoxCasePipeline(
            self.create_task,
            applicator.postprocess_output,
            applicator.divider,
        )
