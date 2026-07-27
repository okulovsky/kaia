from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Optional


@dataclass
class SpecialDay:
    date: datetime
    name: str
    costume: str|None = None
    is_this_day_today: Optional[Callable[[date], bool]] = None

    def matches(self, today: date) -> bool:
        if self.is_this_day_today is not None:
            return self.is_this_day_today(today)
        return (today.month, today.day) == (self.date.month, self.date.day)
