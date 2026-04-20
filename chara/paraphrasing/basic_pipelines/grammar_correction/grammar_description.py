from dataclasses import dataclass
from typing import Any, Callable
from grammatron.grammars.ru import RuDeclension, RuGrammarRule
from grammatron.grammars.de import DeCasus, DeGrammarRule, DeArticleType


@dataclass
class GrammarCategoryDescription:
    grammar_rule_field: str
    caption: str
    values: dict[str, Any]



@dataclass
class GrammarRuleDescription:
    categories: tuple[GrammarCategoryDescription,...]

    @staticmethod
    def for_language(language: str) -> 'GrammarRuleDescription|None':
        if language == 'ru':
            return GrammarRuleDescription(
                categories= (
                    GrammarCategoryDescription(
                        'declension',
                        'падеж',
                        {
                            "Именительный": RuDeclension.NOMINATIVE,
                            "Родительный": RuDeclension.GENITIVE,
                            "Дательный": RuDeclension.DATIVE,
                            "Винительный": RuDeclension.ACCUSATIVE,
                            "Творительный": RuDeclension.INSTRUMENTAL,
                            "Предложный": RuDeclension.PREPOSITIONAL
                        }
                    ),
                ))

        if language == 'de':
            return GrammarRuleDescription(
                categories=(
                    GrammarCategoryDescription(
                        'casus',
                        {c.name: c for c in DeCasus},
                    ),
                    GrammarCategoryDescription(
                        "article_type",
                        {c.name: c for c in DeArticleType},
                        explanation="Which article is suggested for the group in case it's singular: STRONG (no article), WEAR (der/die/das), MIXED (ein/eine)"
                    )
                ))

