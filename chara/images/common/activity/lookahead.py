import calendar
from datetime import date
from .theme import Theme

_SEASON_MONTHS = {
    'winter': {12, 1, 2},
    'spring': {3, 4, 5},
    'summer': {6, 7, 8},
    'autumn': {9, 10, 11},
}


def _add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _months_in_span(start: date, end: date) -> set[int]:
    months = set()
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.add(month)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _next_occurrence(month: int, day: int, today: date) -> date:
    year = today.year
    candidate = date(year, month, min(day, calendar.monthrange(year, month)[1]))
    if candidate < today:
        year += 1
        candidate = date(year, month, min(day, calendar.monthrange(year, month)[1]))
    return candidate


def is_theme_within_lookahead(theme: Theme, today: date, lookahead_span: int) -> bool:
    cutoff = _add_months(today, lookahead_span)

    if theme.special_day is not None:
        occurrence = _next_occurrence(theme.special_day.date.month, theme.special_day.date.day, today)
        return occurrence <= cutoff

    if theme.season is not None:
        season_months = _SEASON_MONTHS.get(theme.season)
        if season_months is None:
            return True
        return len(season_months & _months_in_span(today, cutoff)) > 0

    return True
