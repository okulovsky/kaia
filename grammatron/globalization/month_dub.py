from .language_dispatch_dub import LanguageDispatchDub
from ..dubs import OptionsDub

class MonthDub(LanguageDispatchDub):
    def __init__(self):
        super().__init__(
            en = OptionsDub({
                'January':1,
                'February':2,
                'March':3,
                'April': 4,
                'May': 5,
                'June': 6,
                'July': 7,
                'August': 8,
                'September': 9,
                'October': 10,
                'November': 11,
                'December': 12}),
            ru = OptionsDub({
                'январь': 1,
                'февраль': 2,
                'март': 3,
                'апрель': 4,
                'май': 5,
                'июнь': 6,
                'июль': 7,
                'август': 8,
                'сентябрь': 9,
                'октябрь': 10,
                'ноябрь': 11,
                'декабрь': 12})
        )
