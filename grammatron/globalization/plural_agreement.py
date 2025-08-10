from ..grammars.en import EnPluralAgreement
from ..grammars.ru import RuPluralAgreement
from .language_dispatch_dub import LanguageDispatchSubSequenceDub
from ..dubs import VariableDub

class PluralAgreement(LanguageDispatchSubSequenceDub):
    def __init__(self, amount: VariableDub, entity: str|VariableDub):
        super().__init__(
            en = EnPluralAgreement(amount, entity),
            ru = RuPluralAgreement(amount, entity)
        )
