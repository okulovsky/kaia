import json
from ..template_paraphrasing import ParsedTemplate
from .grammar_description import GrammarRuleDescription
from dataclasses import dataclass
from grammatron import Template, VariableDub
from chara.common.descriptions import Language
import random
from typing import Any

@dataclass
class GrammarModel:
    original_template: Template
    sequence: ParsedTemplate
    target_language_code: str
    target_language_name: str
    grammar_rule: GrammarRuleDescription
    format_example: str|None = None

    def __post_init__(self):
        example = {}
        for field in self.sequence.fragments:
            example[field.name] = {}
            for category in self.grammar_rule.categories:
                example[field.name][category.caption] = random.choice(list(category.values.keys()))
        example = dict(text='...', grammar=example)
        self.format_example = json.dumps(example, indent = 2, ensure_ascii=False).replace('\n','\n\n')

    @staticmethod
    def build(template: Template) -> 'GrammarModel':
        parsed_template = ParsedTemplate.parse_single(template)
        language = parsed_template.original_language
        rule = GrammarRuleDescription.for_language(language)
        return GrammarModel(
            template,
            parsed_template,
            language,
            Language.from_code(language).name,
            rule,
        )

    def apply(self, grammar_advice: Any):
        grammar_advice = grammar_advice['grammar']
        for variable_name, variable_grammar in grammar_advice.items():
            fragment = next((f for f in self.sequence.fragments if f.name == variable_name))
            grammar_rule = fragment.dub.grammar.get_grammar(self.target_language_code)
            for category in self.grammar_rule.categories:
                provided_value = grammar_advice[variable_name][category.caption]
                selected_value = category.values[provided_value]
                setattr(grammar_rule, category.grammar_rule_field, selected_value)


