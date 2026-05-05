from ...dubs import VariableDub, DubParameters, GrammarAdoptableDub, VariableInfo
from dataclasses import dataclass
from .grammar_rule import RuGrammarRule, Declinator, RuCase, RuGender, RuNumber, RuAnimacy
from ..common import IPluralAgreement, WordProcessor

@dataclass
class RuPluralAgreement(IPluralAgreement):
    def __init__(self, amount: VariableDub, entity: str|VariableDub):
        super().__init__(amount, entity)

    def _to_str_internal(self, value, parameters: DubParameters):
        grammar = parameters.grammar_rule
        if not isinstance(grammar, RuGrammarRule):
            grammar = RuGrammarRule()
        entity_text = self.entity.to_str(value, parameters.change_grammar(None))

        words = WordProcessor.words_only(entity_text)
        gender = RuGender.MASCULINE.value
        animacy = RuAnimacy.INANIMATE
        for index in Declinator.choose_words_in_vocabular_form(words):
            parse = Declinator.get_vocabular_form(words[index])
            if parse.tag.POS == 'NOUN':
                if parse.tag.gender is not None:
                    gender = parse.tag.gender
                if parse.tag.animacy == RuAnimacy.ANIMATE.value:
                    animacy = RuAnimacy.ANIMATE
                break
            elif parse.tag.gender is not None:
                gender = parse.tag.gender

        amount_case = grammar.case if grammar.case is not None else RuCase.NOMINATIVE
        amount_value = value[self.amount.name]
        amount_text = self.amount.to_str(value, parameters.change_grammar(RuGrammarRule(amount_case, gender, animacy=animacy)))
        remainder = amount_value % 10

        # For inanimate nouns, accusative = nominative in numeral constructions.
        nominative_like = (amount_case == RuCase.NOMINATIVE or
                           (amount_case == RuCase.ACCUSATIVE and animacy == RuAnimacy.INANIMATE))

        if not nominative_like:
            entity_rule = RuGrammarRule(case=amount_case, number=RuNumber.SINGULAR if remainder == 1 else RuNumber.PLURAL, animacy=animacy)
        elif (amount_value % 100) // 10 == 1:
            entity_rule = RuGrammarRule(case=RuCase.GENITIVE, number=RuNumber.PLURAL, animacy=animacy)
        elif remainder == 1:
            entity_rule = RuGrammarRule(case=amount_case, number=RuNumber.SINGULAR, animacy=animacy)
        elif 2 <= remainder <= 4:
            entity_rule = RuGrammarRule(case=RuCase.GENITIVE, number=RuNumber.MIXED, animacy=animacy)
        else:
            entity_rule = RuGrammarRule(case=RuCase.GENITIVE, number=RuNumber.PLURAL, animacy=animacy)

        entity_text = self.entity.to_str(value, parameters.change_grammar(entity_rule))
        return amount_text+' '+entity_text




