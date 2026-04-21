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
                        'Kasus',
                        {
                            "Nominative": DeCasus.NOMINATIV,
                            "Genitiv": DeCasus.GENITIV,
                            "Dativ": DeCasus.DATIV,
                            "Akkusativ": DeCasus.AKKUSATIV,
                        },
                    ),
                    GrammarCategoryDescription(
                        "article_type",
                        'Artikeltyp',
                        {
                            "kein" : DeArticleType.STRONG,
                            "bestimmter": DeArticleType.WEAK,
                            "unbestimmter": DeArticleType.MIXED
                        },
                    )
                ))

