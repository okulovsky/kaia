from datetime import date
from ..dubs import VariableDub, OrdinalDub, FunctionalTemplateDub
from ..grammars.ru import RuDeclension
from .language_dispatch_dub import LanguageDispatchDub
from .month_dub import MonthDub
from .year_dub import YearDub

DAY = VariableDub("day", OrdinalDub(31))

MONTH = VariableDub("month", MonthDub())

YEAR = VariableDub("year", YearDub())


def from_date(value: date):
    return dict(
        day = value.day,
        month = value.month,
        year = value.year
    )

def to_date(variables: dict):
    day = variables['day']
    month = variables['month']
    if 'year' not in variables:
        year = date.today().year
    else:
        year = variables['year']
    return date(year, month, day)

class DateDub(LanguageDispatchDub):
    def __init__(self):
        sequences = {}
        sequences['en'] = [
            f"{MONTH}, {DAY}",
            f"the {DAY} of {MONTH}",
            f"{MONTH}, {DAY}, {YEAR}",
            f"the {DAY} of {MONTH}, {YEAR}"
        ]
        sequences['ru'] = [
            f"{DAY} {MONTH.grammar.ru(RuDeclension.GENITIVE)}",
            f"{DAY} {MONTH.grammar.ru(RuDeclension.GENITIVE)} {YEAR}"
        ]

        dubs = {key: FunctionalTemplateDub(value, from_date, to_date) for key, value in sequences.items()}
        super().__init__(**dubs)


