from datetime import datetime
from ..common import State
from .state_field_setter import IStateFieldSetter


class SeasonStateFieldSetter(IStateFieldSetter):
    DEFAULT_SEASON_MONTHS = {
        'winter': (12, 1, 2),
        'spring': (3, 4, 5),
        'summer': (6, 7, 8),
        'autumn': (9, 10, 11),
    }

    def __init__(self, season_months: dict[str, tuple[int, ...]] = DEFAULT_SEASON_MONTHS):
        self.month_to_season = {
            month: season
            for season, months in season_months.items()
            for month in months
        }

    def update(self, state: State, now: datetime) -> None:
        state.season = self.month_to_season.get(now.month)
