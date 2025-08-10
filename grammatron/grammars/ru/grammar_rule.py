from typing import Any
from ...dubs import GrammarRule, IDub
from .categories import *
from .declinator import Declinator

class RuGrammarRule(GrammarRule):
    def __init__(self, declension: RuDeclension|str|None = None, gender: RuGender|str|None = None, number: RuNumber|str|None = None):
        self.declension = declension
        self.gender = gender
        self.number = number

    def apply(self, text: str):
        return Declinator.declinate(text, self.declension, self.gender, self.number)


    def to_correct_form(self, text: str, value: Any, dub: 'IDub'):
        return self.apply(text)


    def all_morphological_forms(self, text: str, value: Any, dub: 'IDub') -> tuple[str,...]:
        result = set()
        for declension in RuDeclension:
            for number in RuNumber:
                for gender in RuGender:
                    result.add(Declinator.declinate(text, declension, gender, number))
        return tuple(result)



