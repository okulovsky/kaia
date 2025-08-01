from ..dubs import IDub, GrammarRule
from .ru import *
from .en import *

class GrammarSetter:
    def __init__(self, dub: IDub):
        self.dub = dub

    def _set_grammar(self, language, grammar) -> IDub:
        if not hasattr(self.dub, GrammarRule.FIELD_NAME):
            setattr(self.dub, GrammarRule.FIELD_NAME, {})
        getattr(self.dub, GrammarRule.FIELD_NAME)[language] = grammar
        return self.dub

    def ru(self, declension: RuDeclension|None = None, gender: RuGender|None = None, number: RuNumber|None = None) -> IDub:
        return self._set_grammar(
            'ru',
            RuGrammarRule(declension, gender, number)
        )

    def en(self, plural: bool|None = None):
        return self._set_grammar(
            'en',
            EnGrammarRule(plural)
        )

    @staticmethod
    def get_default_grammar_for_language(language: str) -> GrammarRule|None:
        if language == 'ru':
            return RuGrammarRule()
        if language == 'en':
            return EnGrammarRule()
        return None


