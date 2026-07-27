from datetime import datetime
from ..common import State, SpecialDay
from .state_field_setter import IStateFieldSetter


class SpecialDayStateFieldSetter(IStateFieldSetter):
    def __init__(self, special_days: list[SpecialDay]):
        self.special_days = special_days

    def update(self, state: State, now: datetime) -> None:
        today = now.date()
        for special_day in self.special_days:
            if special_day.matches(today):
                state.special_day = special_day.name
                return
        state.special_day = None
