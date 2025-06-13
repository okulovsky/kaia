from ..core import LanguageDispatchDub, TemplateVariable, FunctionalTemplateDub
from .int_dub import CardinalDub, OrdinalDub
from .options_dub import OptionsDub
from datetime import date


DAY = TemplateVariable(
    "day",
    LanguageDispatchDub(
        en = OrdinalDub(1,31),
    ))

MONTH = TemplateVariable(
    "month",
    LanguageDispatchDub(
        en = OptionsDub({'January':1, 'February':2, 'March':3, 'April': 4, 'May': 5, 'June': 6, 'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}),
))

YEAR_SHORT = TemplateVariable(
    "year_short",
    LanguageDispatchDub(
        en = OrdinalDub(1,50),
    )
)

def from_date(value: date):
    return dict(
        day = value.day,
        month = value.month,
        year_short = value.year%100
    )

def to_date(variables: dict):
    day = variables['day']
    month = variables['month']
    if 'year_short' not in variables:
        year = date.today().year
    else:
        year = 2000 + variables['year_short']
    return date(year, month, day)

class DateDub(LanguageDispatchDub):
    def __init__(self):
        sequences = {}
        sequences['en'] = [
            f"{MONTH}, {DAY}",
            f"the {DAY} of {MONTH}",
            f"{MONTH}, {DAY}, {YEAR_SHORT}",
            f"the {DAY} of {MONTH}, {YEAR_SHORT}"
        ]

        dubs = {key: FunctionalTemplateDub(value, from_date, to_date) for key, value in sequences.items()}
        super().__init__(**dubs)


