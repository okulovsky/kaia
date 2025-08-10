from .language_dispatch_dub import LanguageDispatchDub
from ..dubs import OptionsDub


class WeekdayDub(LanguageDispatchDub):
    def __init__(self):
        super().__init__(
            en = OptionsDub({
                    'Monday': 0,
                    'Tuesday': 1,
                    'Wednesday': 2,
                    'Thursday': 3,
                    'Friday': 4,
                    'Saturday' : 5,
                    'Sunday' : 6
            }),
            ru = OptionsDub({
                'понедельник': 0,
                'вторник': 1,
                'среда': 2,
                'четверг': 3,
                'пятница': 4,
                'суббота': 5,
                'воскресенье': 6
            })
        )
