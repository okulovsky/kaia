from pandas.core.window.doc import template_see_also

from ..common import TemplateParaphraseCase, ParsedTemplate
from grammatron import Template
from chara.common import Character
from grammatron import TemplateContext

class UtteranceParaphraseCase(TemplateParaphraseCase):
    def __init__(self,
                 template: Template,
                 target_language_code: str,
                 character: Character|None = None,
                 user: Character|None = None,
                 relationship: str|None = None,
                 variations_per_template: int = 10
                 ):
        super().__init__(template, target_language_code)
        self.character = character
        self.user = user
        self.relationship = relationship
        self.variations_per_template = variations_per_template

        self.samples: tuple[str, ...]|None = None
        self.variables_description: tuple[str, ...]|None = None
        self.context: TemplateContext|None = None
        self.reply_to_examples: tuple[str, ...] | None = None


    def prepare(self):
        self.samples = tuple(c.representation for c in self.parsed_template.all_alternatives)
        self.variables_description = tuple(c.description for c in self.parsed_template.fragments)
        self.context = self.original_template.get_context()
        if self.context.reply_to is not None:
            self.reply_to_examples = tuple(
                parsed.representation
                for template in self.context.reply_to
                for parsed in ParsedTemplate.parse(template)
            )