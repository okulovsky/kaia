from ...dubs import VariableDub, ISequenceDub, GrammarAdoptableDub, ConstantDub, ISubSequenceDub

class IPluralAgreement(ISequenceDub):
    def __init__(self, amount: VariableDub, entity: str|VariableDub):
        self.amount = amount
        if isinstance(entity, str):
            entity = GrammarAdoptableDub(entity)
        self.entity: VariableDub|GrammarAdoptableDub = entity

    def get_sequence(self) -> tuple[ISubSequenceDub, ...]:
        return (
            self.amount,
            ConstantDub(' '),
            self.entity
        )