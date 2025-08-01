from ..common import IPluralAgreement
from .grammar_rule import EnGrammarRule
from ...dubs import DubParameters, VariableDub

class EnPluralAgreement(IPluralAgreement):
    def __init__(self, amount: VariableDub, entity: str|VariableDub):
        super().__init__(amount, entity)
        
    
    def _to_str_internal(self, value, parameters: DubParameters|None = None):
        numeral_str = self.amount.to_str(value, parameters)
        amount = value[self.amount.name]
        target_rule = EnGrammarRule(plural=amount!=1)
        entity_text = self.entity.to_str(value, parameters.change_grammar(target_rule))
        return f'{numeral_str} {entity_text}'





