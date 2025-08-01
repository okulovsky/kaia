from typing import Any
from ...dubs import GrammarRule, OptionsDub, GrammarAdoptableDub, IDub
from copy import copy
from .word_tools import EnglishWordTools

class EnGrammarRule(GrammarRule):
    def __init__(self, plural: bool|None = None):
        self.plural = plural

    def merge_with_lower_priority(self, rule: GrammarRule):
        if not isinstance(rule, EnGrammarRule):
            raise ValueError("Must only be merged with EnGrammarRule")
        result = copy(self)
        if result.plural is None:
            result.plural = rule.plural
        return result

    def to_correct_form(self, text: str, value: Any, dub: 'IDub'):
        if not isinstance(dub, OptionsDub) and not isinstance(dub, GrammarAdoptableDub):
            return text
        if self.plural:
            return EnglishWordTools.text_to_plural(text)
        return text

    def all_morphological_forms(self, text: str, value: Any, dub: 'IDub') -> tuple[str,...]:
        if not isinstance(dub, OptionsDub) and not isinstance(dub, GrammarAdoptableDub):
            return (text,)
        return (text, EnglishWordTools.text_to_plural(text))


