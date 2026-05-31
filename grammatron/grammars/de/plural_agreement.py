from ..common import IPluralAgreement
from .grammar_rule import DeGrammarRule
from .categories import DeCasus, DeNumerus, DeArticleType
from .declinator import DeDeclinator
from ...dubs import DubParameters, VariableDub


class DePluralAgreement(IPluralAgreement):
    def __init__(self, amount: VariableDub, entity: str | VariableDub):
        super().__init__(amount, entity)

    def _to_str_internal(self, value, parameters: DubParameters | None = None):
        grammar = parameters.grammar_rule if isinstance(parameters.grammar_rule, DeGrammarRule) else DeGrammarRule()

        amount_value = value[self.amount.name]
        numerus = DeNumerus.SINGULAR if amount_value == 1 else DeNumerus.PLURAL
        casus = grammar.casus or DeCasus.NOMINATIV
        article = DeArticleType.MIXED if amount_value == 1 else DeArticleType.STRONG

        if amount_value != 1:
            amount_text = self.amount.to_str(value, parameters) + " "
        else:
            amount_text = ""

        entity_rule = DeGrammarRule(
            casus=casus,
            genus=grammar.genus,
            numerus=numerus,
            article_type=article,
        )

        entity_text = self.entity.to_str(value, parameters.change_grammar(entity_rule))

        phrase = f'{amount_text}{entity_text}'

        return phrase
