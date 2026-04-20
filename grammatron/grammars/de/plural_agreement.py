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

        amount_rule = DeGrammarRule(
            casus=casus,
            genus=grammar.genus,
            numerus=numerus,
            article_type=None,
        )
        amount_text = self.amount.to_str(value, parameters.change_grammar(amount_rule))

        # Entity is inflected for case/number but WITHOUT article — the article
        # (if requested) is prepended to the whole phrase: "die drei Hunde".
        entity_rule = DeGrammarRule(
            casus=casus,
            genus=grammar.genus,
            numerus=numerus,
            article_type=None,
        )
        entity_text = self.entity.to_str(value, parameters.change_grammar(entity_rule))

        phrase = f'{amount_text} {entity_text}'

        if grammar.article_type is not None and grammar.article_type != DeArticleType.STRONG:
            # Determine genus from entity text (genus detection happens inside declinate,
            # but here we need it for the article only). Reuse DeDeclinator's genus lookup.
            from ..common import WordProcessor
            words = [f.fragment for f in WordProcessor.word_split(entity_text) if f.is_word]
            genus = grammar.genus
            if genus is None:
                for w in words:
                    if w and w[0].isupper():
                        g = DeDeclinator.get_noun_genus(w)
                        if g is not None:
                            genus = g
                            break
            if genus is None:
                from .categories import DeGenus
                genus = DeGenus.MASKULINUM
            article = DeDeclinator.get_article(casus, genus, numerus, grammar.article_type)
            if article:
                phrase = f'{article} {phrase}'

        return phrase
