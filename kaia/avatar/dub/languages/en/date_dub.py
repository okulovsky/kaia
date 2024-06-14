from typing import *
from .ints import OrdinalDub, CardinalDub
from ...core import UnionDub, DictDub, SetDub, IRandomizableDub, SetUnionDub
from datetime import date, datetime, timedelta
from numpy.random import RandomState
from enum import Enum




class YearDub(UnionDub):
    def __init__(self):
        super().__init__(
            UnionDub.create_sequences(
                strings = [
                    '{year_high} {year_low}',
                    '{year}',
                    '{year_low}'
                ],
                dubs = dict(
                    year_high = CardinalDub(0, 99),
                    year_low = CardinalDub(0, 99),
                    year = SetUnionDub(OrdinalDub(1900, 2100), CardinalDub(1900, 2100))
                ),
                sequence_prefix='YearDub'
            ),
            value_to_dict =YearDub.year_to_high_low,
            dict_to_value = YearDub.high_low_to_year
        )

    @staticmethod
    def year_to_high_low(year: int):
        return dict(year_high=year // 100, year_low=year % 100)

    @staticmethod
    def high_low_to_year(d):
        if 'year' in d:
            return d['year']
        if 'year_high' in d:
            return d['year_high'] * 100 + d['year_low']
        else:
            return 2000 + d['year_low']


months = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

class DateDub(UnionDub, IRandomizableDub):
    def __init__(self, output_without_year: bool = False):
        self.output_without_year = output_without_year

        super().__init__(
            UnionDub.create_sequences(
                strings = [
                    "{month} {day}, year {year}",
                    "{month} {day}",
                    "{day} of {month}",
                    "{day} of {month}, year {year}"
                ],
                dubs=dict(
                    month = DictDub(months, 'MonthsDub'),
                    day = SetUnionDub(OrdinalDub(1,31), CardinalDub(1,31)),
                    year = YearDub()
                ),
                sequence_prefix = 'DateDub'
            ),
            value_to_dict=self.date_to_dict,
            dict_to_value=DateDub.dict_to_date
        )

    def get_name(self):
        return 'DateDub'

    def get_random_value(self, random_state: Optional[RandomState] = RandomState()):
        return date(2020, 1, 1) + timedelta(days = random_state.randint(1, 5000))

    def date_to_dict(self, dt: Union[date, datetime]):
        if isinstance(dt, datetime):
            dt = dt.date()
        result = dict(
            month=dt.month,
            day=dt.day,
        )
        if not self.output_without_year:
            result['year'] = dt.year
        return result

    @staticmethod
    def dict_to_date(d):
        if 'year' not in d:
            d['year'] = date.today().year
        return date(d['year'], d['month'], d['day'])
