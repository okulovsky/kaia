from grammatron import *
from dataclasses import dataclass
from ..common import ParaphraseCase, ParsedTemplate
from chara.common import Character

@dataclass
class JinjaTemplateModel:
    template: ParsedTemplate
    samples: tuple[str,...]
    variables_description: tuple[str,...]
    context: TemplateContext

    has_description: bool = False
    has_context: bool = False
    reply_to_examples: tuple[str,...]|None = None

    def __post_init__(self):
        self.context = self.template.template.get_context()
        self.has_description = len(self.variables_description) > 0
        self.has_context = (
                self.context.context is not None
                or self.context.reply_to is not None
                or self.context.reply_details is not None
        )

        if self.context.reply_to is not None:
            self.reply_to_examples = tuple(
                sequence.representation
                for template in self.context.reply_to
                for parsed in ParsedTemplate.parse(template)
                for sequence in parsed.sequences
            )

@dataclass
class JinjaModel:
    model: JinjaTemplateModel
    character: Character|None
    user: Character|None
    relationship: str|None
    language: str = 'en'

    @staticmethod
    def build_from_case(case: ParaphraseCase) -> 'JinjaModel':
        samples = tuple(sequence.representation for sequence in case.template.sequences)
        template_model = JinjaTemplateModel(
            case.template,
            samples,
            tuple(c.description for c in case.template.sequences[0].unwrapped_sequence.fragment_to_description.values()),
            case.template.template.get_context(),
        )
        return JinjaModel(
            template_model,
            case.character,
            case.user,
            case.relationship,
            case.language
        )
