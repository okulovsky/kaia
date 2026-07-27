from datetime import datetime
from ..common import State
from .state_field_setter import IStateFieldSetter


class TimeOfDayStateFieldSetter(IStateFieldSetter):
    DEFAULT_BOUNDARIES = (
        (5, 'morning'),
        (11, 'day'),
        (17, 'evening'),
        (22, 'night'),
    )

    def __init__(self, boundaries: tuple[tuple[int, str], ...] = DEFAULT_BOUNDARIES):
        self.boundaries = boundaries

    def _time_of_day(self, hour: int) -> str:
        result = self.boundaries[-1][1]
        for start_hour, name in self.boundaries:
            if hour >= start_hour:
                result = name
        return result

    def update(self, state: State, now: datetime) -> None:
        state.time_of_day = self._time_of_day(now.hour)
