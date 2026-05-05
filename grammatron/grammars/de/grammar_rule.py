from typing import Any
from copy import copy
from ...dubs import GrammarRule, IDub, OptionsDub, GrammarAdoptableDub, ToStrDub
from .categories import DeCasus, DeGenus, DeNumerus, DeArticleType
from .declinator import DeDeclinator


class DeGrammarRule(GrammarRule):
    def __init__(
            self,
            casus: DeCasus | None = None,
            genus: DeGenus | None = None,
            numerus: DeNumerus | None = None,
            article_type: DeArticleType | None = None,
    ):
        self.casus = casus
        self.genus = genus
        self.numerus = numerus
        self.article_type = article_type

    def get_language_name(self):
        return 'de'

    def merge_with_lower_priority(self, rule: GrammarRule) -> 'DeGrammarRule':
        if not isinstance(rule, DeGrammarRule):
            return self
        result = copy(self)
        if result.casus is None:
            result.casus = rule.casus
        if result.genus is None:
            result.genus = rule.genus
        if result.numerus is None:
            result.numerus = rule.numerus
        if result.article_type is None:
            result.article_type = rule.article_type
        return result

    def to_correct_form(self, text: str, value: Any, dub: 'IDub') -> str:
        if not isinstance(dub, (OptionsDub, GrammarAdoptableDub, ToStrDub)):
            return text
        return DeDeclinator.declinate(
            text,
            casus=self.casus,
            genus=self.genus,
            numerus=self.numerus,
            article_type=self.article_type,
        )

    def all_morphological_forms(self, text: str, value: Any, dub: 'IDub') -> tuple[str, ...]:
        if not isinstance(dub, (OptionsDub, GrammarAdoptableDub)):
            return (text,)
        result: set[str] = set()
        for casus in DeCasus:
            for numerus in DeNumerus:
                for genus in DeGenus:
                    for article_type in DeArticleType:
                        result.add(DeDeclinator.declinate(
                            text,
                            casus=casus,
                            genus=genus,
                            numerus=numerus,
                            article_type=article_type,
                        ))
        return tuple(result)
