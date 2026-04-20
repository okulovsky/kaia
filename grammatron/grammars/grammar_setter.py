from ..dubs import IDub, GrammarRule
from .ru import *
from .en import *
from .de import *

class GrammarSetter:
    def __init__(self, dub: IDub):
        self.dub = dub

    def _ensure_grammar_field(self) -> dict[str, GrammarRule]:
        if not hasattr(self.dub, GrammarRule.FIELD_NAME):
            setattr(self.dub, GrammarRule.FIELD_NAME, {})
        return getattr(self.dub, GrammarRule.FIELD_NAME)

    def set_grammar(self, language, grammar) -> IDub:
        grammars = self._ensure_grammar_field()
        grammars[language] = grammar
        return self.dub

    def get_grammar(self, language):
        grammars = self._ensure_grammar_field()
        if language not in grammars:
            grammars[language] = GrammarSetter.get_default_grammar_for_language(language)
        return grammars[language]

    def ru(self, declension: RuDeclension|None = None, gender: RuGender|None = None, number: RuNumber|None = None) -> IDub:
        return self.set_grammar(
            'ru',
            RuGrammarRule(declension, gender, number)
        )

    def en(self, plural: bool|None = None):
        return self.set_grammar(
            'en',
            EnGrammarRule(plural)
        )

    def de(
            self,
            casus: DeCasus|None = None,
            genus: DeGenus|None = None,
            numerus: DeNumerus|None = None,
            article_type: DeArticleType|None = None,
    ) -> IDub:
        return self.set_grammar(
            'de',
            DeGrammarRule(casus, genus, numerus, article_type)
        )

    @staticmethod
    def get_default_grammar_for_language(language: str) -> GrammarRule|None:
        if language == 'ru':
            return RuGrammarRule()
        if language == 'en':
            return EnGrammarRule()
        if language == 'de':
            return DeGrammarRule()
        return None


