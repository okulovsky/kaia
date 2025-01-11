from typing import *
from dataclasses import dataclass
from enum import Enum
from datetime import time, datetime, timedelta, date
from abc import ABC, abstractmethod


class Weekdays(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6


class IRepetition(ABC):
    @abstractmethod
    def accepts_date(self, date: date) -> bool:
        pass

    def get_acceptable_dates(self, begin: datetime, end: datetime) -> Iterator[date]:
        begin_date = datetime(begin.year, begin.month, begin.day)
        while True:
            if begin_date > end:
                break
            if begin_date >= begin:
                if self.accepts_date(begin_date.date()):
                    yield begin_date.date()
            begin_date = begin_date + timedelta(days=1)



class WeekdayRepetition(IRepetition):
    def __init__(self, days: Weekdays | int | Iterable[Weekdays|int]):
        try:
            iterator = iter(days)
            iterable = True
        except:
            iterable = False
        if not iterable:
            days = [days]
        parsed = []
        for i, day in enumerate(days):
            if isinstance(day, int):
                parsed.append(Weekdays(day))
            elif isinstance(day, Weekdays):
                parsed.append(day)
            else:
                raise ValueError(f"Argument {i} should be Weekday or int, but was {day}")
        self._days = tuple(c.value for c in parsed)


    def accepts_date(self, date: date) -> bool:
        return date.weekday() in self._days


class EveryDayRepetition(IRepetition):
    def accepts_date(self, date: date) -> bool:
        return True


class CombinedRepetition(IRepetition):
    def __init__(self, repetitions: Iterable[IRepetition]):
        self.repetitions = tuple(repetitions)

    def accepts_date(self, date: date) -> bool:
        for rep in self.repetitions:
            if not rep.accepts_date(date):
                return False
        return True



@dataclass
class ScheduledTime:
    time: time
    duration: timedelta | None = None
    repetition: IRepetition = EveryDayRepetition()

    def all_intersections_with_interval(self, begin: datetime, end: datetime) -> Iterator[datetime]:
        if begin > end:
            raise ValueError(f'`begin` must not be greater than `end`, but were: {begin}, {end}')
        begin_1 = datetime(begin.year, begin.month, begin.day, self.time.hour, self.time.minute, self.time.second)
        while True:
            if not self.repetition.accepts_date(begin_1.date()):
                begin_1 += timedelta(days=1)
                continue
            if begin_1 > end:
                break
            if self.duration is None:
                if begin_1 >= begin and begin_1 <= end:
                    yield begin_1
            else:
                end_1 = begin_1 + self.duration
                if begin_1 <= end and end_1 >= begin:
                    yield begin_1
            begin_1 += timedelta(days=1)

    def intersects_with_interval(self, begin: datetime, end: datetime) -> bool:
        for _ in self.all_intersections_with_interval(begin, end):
            return True
        return False








    


