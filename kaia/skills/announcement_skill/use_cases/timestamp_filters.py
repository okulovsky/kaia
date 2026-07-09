from ..core import IAnnouncementFilter, AnnouncementEnvironment
from enum import Enum
from datetime import datetime, timedelta, date, time
from abc import abstractmethod
from dataclasses import dataclass
from random import randint
from typing import ClassVar

class Weekdays(Enum):
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6

class ITimestampBasedAnnouncementFilter(IAnnouncementFilter):
    @abstractmethod
    def should_announce_at_datetime(self, timestamp: datetime ) -> bool:
        pass

    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        return self.should_announce_at_datetime(env.current_time)


@dataclass
class Calendar(ITimestampBasedAnnouncementFilter):
    weekdays: list[Weekdays]|None = None
    month_indices: list[int]|None = None

    Weekdays: ClassVar = Weekdays

    def should_announce_at_datetime(self, timestamp: datetime) -> bool:
        if self.weekdays is not None:
            day = Weekdays(timestamp.weekday())
            if day not in self.weekdays:
                return False
        if self.month_indices is not None:
            month_index = (timestamp.day-1)//7 + 1
            if month_index not in self.month_indices:
                return False
        return True

    def workdays(self):
        return Calendar(
            [Weekdays.Monday, Weekdays.Tuesday, Weekdays.Wednesday, Weekdays.Thursday, Weekdays.Friday],
            self.month_indices
        )

    def weekend(self):
        return Calendar(
            [Weekdays.Saturday, Weekdays.Sunday],
            self.month_indices
        )

    def even_weeks(self):
        return Calendar(self.weekdays, [2, 4])

    def odd_weeks(self):
        return Calendar(self.weekdays, [1, 3, 5])


def _float_to_time(f) -> time:
    hours = int(f)
    minutes = int(round((f - hours) * 100))
    return time(hours, minutes)

class Hours(ITimestampBasedAnnouncementFilter):
    def __init__(self, from_hour: float, to_hour: float):
        self.from_time = _float_to_time(from_hour)
        self.to_time = _float_to_time(to_hour)

    def should_announce_at_datetime(self, timestamp: datetime) -> bool:
        return timestamp.time() >= self.from_time and timestamp.time() <= self.to_time


class RandomTime(ITimestampBasedAnnouncementFilter):
    def __init__(self, from_hour: float, to_hour: float, percentage: float):
        self.from_time = _float_to_time(from_hour)
        self.to_time = _float_to_time(to_hour)

        d = date.today()

        self._full_span_in_seconds = (datetime.combine(d, self.to_time) - datetime.combine(d, self.from_time)).total_seconds()
        self._choosen_span_in_seconds = int(self._full_span_in_seconds * percentage)

        self._date_to_choosen_time = {}

    def _get_start_for_date(self, date: date):
        if date not in self._date_to_choosen_time:
            self._date_to_choosen_time[date] = randint(0, self._choosen_span_in_seconds)
        return datetime.combine(date, self.from_time) + timedelta(seconds=self._date_to_choosen_time[date])


    def should_announce_at_datetime(self, timestamp: datetime ) -> bool:
        begin = self._get_start_for_date(timestamp.date())
        return timestamp >= begin and timestamp <= begin + timedelta(seconds=self._choosen_span_in_seconds)



class ExactDay(ITimestampBasedAnnouncementFilter):
    def __init__(self, day: int, month: int):
        self.day = day
        self.month = month

    def should_announce_at_datetime(self, timestamp: datetime) -> bool:
        return timestamp.day == self.day and timestamp.month == self.month


