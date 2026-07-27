import json
from dataclasses import dataclass, fields
from typing import Any, Callable, get_type_hints
from brainbox.deciders import Ollama
from foundation_kaia.marshalling import Serializer, BoolHandler, EnumHandler, NoneHandler, IntHandler, FloatHandler
from .json_parser import parse_json
from .prompt_task_builder import PromptTaskBuilder


@dataclass
class Question:
    field_name: str
    question: str
    type: type
    options: list[Any]|None = None
    is_closed: bool|None = None

    def __post_init__(self):
        serializer = Serializer.parse(self.type)
        non_none = [h for h in serializer.handlers if not isinstance(h, NoneHandler)]
        type_is_closed = len(non_none) == 1 and isinstance(non_none[0], (BoolHandler, EnumHandler))
        if type_is_closed:
            handler = non_none[0]
            domain = [True, False] if isinstance(handler, BoolHandler) else list(handler.enum_type)
            if serializer.is_nullable:
                domain = domain + [None]
            self.options = domain
        elif not self.options:
            if len(non_none) == 1 and isinstance(non_none[0], IntHandler):
                self.options = [1, 2, 3]
            elif len(non_none) == 1 and isinstance(non_none[0], FloatHandler):
                self.options = [1.0, 1.5, 2.0]
            else:
                raise ValueError(
                    f"Question `{self.field_name}` has an open type `{self.type}`, "
                    f"so at least one example value must be provided in `options`"
                )
        if self.is_closed is None:
            self.is_closed = type_is_closed


@dataclass
class QuestionList:
    questions: list[Question]
    dataclass_type: type|None = None

    @staticmethod
    def from_dataclass(dataclass_type: type) -> 'QuestionList':
        hints = get_type_hints(dataclass_type)
        questions = [
            Question(f.name, f.metadata['desc'], hints[f.name], options=f.metadata.get('options'))
            for f in fields(dataclass_type)
        ]
        return QuestionList(questions, dataclass_type)

    def get_description(self) -> str:
        lines = []
        for q in self.questions:
            serializer = Serializer.parse(q.type)
            rendered = ", ".join(f"`{json.dumps(serializer.to_json(v))}`" for v in q.options)
            suffix = "" if q.is_closed else " etc"
            lines.append(f"`{q.field_name}`: {q.question} ({rendered}{suffix})")
        return "\n".join(lines)

    def get_example(self) -> str:
        example = {q.field_name: Serializer.parse(q.type).to_json(q.options[0]) for q in self.questions}
        return json.dumps(example, indent=2)

    def get_format(self) -> dict:
        return {
            "type": "object",
            "properties": {q.field_name: Serializer.parse(q.type).to_json_schema().to_dict() for q in self.questions},
            "required": [q.field_name for q in self.questions],
        }

    def create_task_builder(self, model: str, intro: Callable[[Any], str]) -> PromptTaskBuilder:
        def prompt(case) -> str:
            return (
                f"{intro(case)}\n\n"
                f"{self.get_description()}\n\n"
                f"Answer these questions in JSON format, e.g.\n\n"
                f"```\n{self.get_example()}\n```\n\n"
                f"Do not provide any comments or explanations."
            )
        return PromptTaskBuilder(model, prompt, options=Ollama.Options(format=self.get_format()))

    def parse(self, s: str) -> dict|Any:
        raw = parse_json(s)
        if self.dataclass_type is not None:
            return Serializer.parse(self.dataclass_type).from_json(raw)
        return {q.field_name: Serializer.parse(q.type).from_json(raw[q.field_name]) for q in self.questions}
