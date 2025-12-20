from ...dubs import VariableDub, DubParameters, GrammarAdoptableDub, VariableInfo
from dataclasses import dataclass
from .grammar_rule import RuGrammarRule, Declinator, RuDeclension, RuGender, RuNumber
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
        for index in Declinator.choose_words_in_vocabular_form(words):
            parse = Declinator.get_vocabular_form(words[index])
            if parse.tag.gender is not None:
                gender = parse.tag.gender
                break

        amount_declension = grammar.declension if grammar.declension is not None else RuDeclension.NOMINATIVE
        amount_value = value[self.amount.name]
        amount_text = self.amount.to_str(value, parameters.change_grammar(RuGrammarRule(amount_declension, gender)))
        remainder = amount_value%10

        if amount_declension != RuDeclension.NOMINATIVE:
            entity_rule = RuGrammarRule(declension=amount_declension, number=RuNumber.SINGULAR if remainder==1 else RuNumber.PLURAL)
        elif (amount_value%100)//10 == 1:
            entity_rule = RuGrammarRule(declension=RuDeclension.GENITIVE, number=RuNumber.PLURAL)
        elif remainder == 1:
            entity_rule = RuGrammarRule(declension=RuDeclension.NOMINATIVE, number=RuNumber.SINGULAR)
        elif 2 <= remainder <= 4:
            entity_rule = RuGrammarRule(declension=RuDeclension.GENITIVE, number=RuNumber.SINGULAR)
        else:
            entity_rule = RuGrammarRule(declension=RuDeclension.GENITIVE, number=RuNumber.PLURAL)

        entity_text = self.entity.to_str(value, parameters.change_grammar(entity_rule))
        return amount_text+' '+entity_text




