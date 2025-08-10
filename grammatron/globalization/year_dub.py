from ..dubs import VariableDub, OrdinalDub, CardinalDub, FunctionalTemplateDub
from .language_dispatch_dub import LanguageDispatchDub
from ..grammars.ru import RuDeclension, RuGender


def to_value(v: dict):
    if v['year'] < 50:
        return 2000+v['year']
    elif v['year'] < 100:
        return 1900+v['year']
    else:
        return v['year']

def from_value(v: int):
    if v > 2000 and v<2050:
        return dict(year = v-2000)
    if v < 2000 and v > 1950:
        return dict(year = v-1900)
    return dict(year=v)


class YearDub(LanguageDispatchDub):
    def __init__(self):
        sequences = {}
        sequences['en'] = FunctionalTemplateDub(
            [f"{VariableDub('year', OrdinalDub(2100))}"],
            value_to_variables=from_value,
            variables_to_value=to_value
        )
        sequences['ru'] = FunctionalTemplateDub(
            [f"{VariableDub('year', OrdinalDub(2100).grammar.ru(declension=RuDeclension.GENITIVE, gender=RuGender.MASCULINE))}"],
            value_to_variables=from_value,
            variables_to_value=to_value
        )
        super().__init__(**sequences)





















