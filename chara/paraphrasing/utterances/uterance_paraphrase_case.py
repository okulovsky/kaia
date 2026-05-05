from __future__ import annotations
from ..common import ParaphraseCase, ParsedTemplate
from grammatron import Template
from chara.common.descriptions import Character
from grammatron import TemplateContext
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .stats_builder import ParaphraseStats

class UtteranceParaphraseCase(ParaphraseCase):
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

        self.stats: ParaphraseStats|None = None

        self.samples: tuple[str, ...]|None = None
        self.context: TemplateContext|None = None
        self.reply_to_examples: tuple[str, ...] | None = None


    def prepare(self):
        self.samples = tuple(c.representation for c in self.parsed_template.all_alternatives)
        self.context = self.original_template.get_context()
        if self.context.reply_to is not None:
            self.reply_to_examples = tuple(
                parsed.representation
                for template in self.context.reply_to
                for parsed in ParsedTemplate.parse(template)
            )