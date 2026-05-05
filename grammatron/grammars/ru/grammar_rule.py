from typing import Any
from copy import copy
from ...dubs import GrammarRule, IDub
from .categories import RuCase, RuGender, RuNumber, RuAnimacy
from .declinator import Declinator

class RuGrammarRule(GrammarRule):
    def __init__(self, case: RuCase|str|None = None, gender: RuGender|str|None = None, number: RuNumber|str|None = None, animacy: RuAnimacy|str|None = None):
        self.case = case
        self.gender = gender
        self.number = number
        self.animacy = animacy

    def get_language_name(self):
        return 'ru'

    def merge_with_lower_priority(self, rule: GrammarRule):
        if not isinstance(rule, RuGrammarRule):
            return self
        result = copy(self)
        if result.case is None:
            result.case = rule.case
        if result.gender is None:
            result.gender = rule.gender
        if result.number is None:
            result.number = rule.number
        if result.animacy is None:
            result.animacy = rule.animacy
        return result

    def apply(self, text: str):
        return Declinator.declinate(text, self.case, self.gender, self.number, self.animacy)


    def to_correct_form(self, text: str, value: Any, dub: 'IDub'):
        return self.apply(text)


    def all_morphological_forms(self, text: str, value: Any, dub: 'IDub') -> tuple[str,...]:
        result = set()
        for case in RuCase:
            for number in RuNumber:
                for gender in RuGender:
                    result.add(Declinator.declinate(text, case, gender, number))
        return tuple(result)



