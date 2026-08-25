import dataclasses
from typing import Any, Callable

from brainbox.deciders import Ollama
from foundation_kaia.prompters import Address, AddressLike

from .step import LLMRequestStep
from .questions import QuestionList


class Questionnaire(LLMRequestStep):
    """Asks a `QuestionList` and parses the answers back.

    The list is either given directly, derived from a dataclass, or read off the case
    by address, which is what the per-scene and per-drawing question sets need.

    The step owns the whole prompt: an intro, then the questions, the JSON instruction
    and the example, all generated from the list. The intro is either the `intro`
    argument or whatever an earlier prompt step produced -- a template rendering the
    scene, say -- but never both. Nothing else renders the questions.
    """

    def __init__(self,
                 questions: QuestionList|type|AddressLike,
                 intro: str|Callable[[Any], str]|None = None,
                 ):
        self.questions = questions
        self.intro = intro
        self._address = None
        if isinstance(questions, QuestionList):
            self._questions = questions
        elif isinstance(questions, type):
            if not dataclasses.is_dataclass(questions):
                raise ValueError(f"A questionnaire type must be a dataclass, but {questions} is not")
            self._questions = QuestionList.from_dataclass(questions)
        else:
            self._questions = None
            self._address = Address.parse(questions)

    def resolve(self, case: Any) -> QuestionList:
        if self._questions is not None:
            return self._questions
        questions = self._address.get(case)
        if not isinstance(questions, QuestionList):
            raise ValueError(f"Address `{self._address}` was expected to hold a QuestionList, got {type(questions)}")
        return questions

    def _get_intro(self, case: Any, arguments: dict) -> str|None:
        produced = arguments.get('prompt', None)
        if self.intro is None:
            return produced
        if produced is not None:
            raise ValueError(
                "Questionnaire was given an intro, but an earlier step already produced a prompt. "
                "The intro comes either from the argument or from a template, not from both."
            )
        return self.intro(case) if callable(self.intro) else self.intro

    def fill_arguments(self, case: Any, template_entities: dict, arguments: dict):
        questions = self.resolve(case)
        intro = self._get_intro(case, arguments)
        parts = []
        if intro is not None and intro.strip():
            parts.append(intro.strip())
        parts.append(questions.get_description())
        parts.append(f"Answer these questions in JSON format, e.g.\n\n```\n{questions.get_example()}\n```")
        parts.append("Do not provide any comments or explanations.")
        arguments['prompt'] = "\n\n".join(parts)

    def update_options(self, case: Any, options: Ollama.Options|None) -> Ollama.Options|None:
        if options is not None and options.format is not None:
            raise ValueError(
                "Questionnaire cannot set the answer format because it is already set. "
                "Questionnaire and ResultTypization both describe the expected answer and "
                "are not meant to be combined in one request."
            )
        return options + Ollama.Options(format=self.resolve(case).get_format())

    def get_parser(self):
        def parse(case: Any, output: str) -> Any:
            return self.resolve(case).parse(output)
        return parse
