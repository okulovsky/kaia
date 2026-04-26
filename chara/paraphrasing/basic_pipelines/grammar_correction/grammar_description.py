from dataclasses import dataclass
from typing import Any, Callable
from grammatron.grammars.ru import RuCase, RuGrammarRule
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
                        'case',
                        'падеж',
                        {
                            "Именительный": RuCase.NOMINATIVE,
                            "Родительный": RuCase.GENITIVE,
                            "Дательный": RuCase.DATIVE,
                            "Винительный": RuCase.ACCUSATIVE,
                            "Творительный": RuCase.INSTRUMENTAL,
                            "Предложный": RuCase.PREPOSITIONAL
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

