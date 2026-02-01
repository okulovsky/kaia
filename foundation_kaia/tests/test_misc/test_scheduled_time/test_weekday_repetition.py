from unittest import TestCase
from datetime import date, datetime
from foundation_kaia.misc.scheduled_time import WeekdayRepetition, Weekdays


class WeekdayRepetitionConstructorTestCase(TestCase):
    def test_single_weekday_enum(self):
        rep = WeekdayRepetition(Weekdays.Monday, None)
        self.assertTrue(rep.accepts_date(date(2026, 2, 2)))  # Monday
        self.assertFalse(rep.accepts_date(date(2026, 2, 3)))  # Tuesday

    def test_single_int(self):
        rep = WeekdayRepetition(0, None)  # Monday
        self.assertTrue(rep.accepts_date(date(2026, 2, 2)))
        self.assertFalse(rep.accepts_date(date(2026, 2, 3)))

    def test_list_of_weekday_enums(self):
        rep = WeekdayRepetition([Weekdays.Monday, Weekdays.Friday], None)
        self.assertTrue(rep.accepts_date(date(2026, 2, 2)))   # Monday
        self.assertTrue(rep.accepts_date(date(2026, 2, 6)))   # Friday
        self.assertFalse(rep.accepts_date(date(2026, 2, 4)))  # Wednesday

    def test_list_of_ints(self):
        rep = WeekdayRepetition([0, 4], None)  # Monday, Friday
        self.assertTrue(rep.accepts_date(date(2026, 2, 2)))
        self.assertTrue(rep.accepts_date(date(2026, 2, 6)))
        self.assertFalse(rep.accepts_date(date(2026, 2, 4)))

    def test_mixed_list(self):
        rep = WeekdayRepetition([Weekdays.Tuesday, 4], None)
        self.assertTrue(rep.accepts_date(date(2026, 2, 3)))   # Tuesday
        self.assertTrue(rep.accepts_date(date(2026, 2, 6)))   # Friday
        self.assertFalse(rep.accepts_date(date(2026, 2, 2)))  # Monday

    def test_invalid_type_in_list_raises(self):
        with self.assertRaises(ValueError):
            WeekdayRepetition(["Monday"], None)

    def test_invalid_int_raises(self):
        with self.assertRaises(ValueError):
            WeekdayRepetition(7, None)


class WeekdayRepetitionAcceptsDateTestCase(TestCase):
    def test_all_weekdays(self):
        for day in Weekdays:
            rep = WeekdayRepetition(day, None)
            # 2026-02-02 is Monday (weekday 0), so day.value offset gives us each day
            target = date(2026, 2, 2 + day.value)
            self.assertTrue(rep.accepts_date(target), f"{day} should accept {target}")
            # The next day should not be accepted (unless it wraps)
            other = date(2026, 2, 2 + ((day.value + 1) % 7))
            self.assertFalse(rep.accepts_date(other), f"{day} should reject {other}")

    def test_no_allowed_weeks_accepts_every_occurrence(self):
        rep = WeekdayRepetition(Weekdays.Monday, None)
        # All Mondays in February 2026
        mondays = [date(2026, 2, 2), date(2026, 2, 9), date(2026, 2, 16), date(2026, 2, 23)]
        for d in mondays:
            self.assertTrue(rep.accepts_date(d))


class WeekdayRepetitionAllowedWeeksTestCase(TestCase):
    def test_first_week_only(self):
        rep = WeekdayRepetition(Weekdays.Monday, [0])
        # February 2026 Mondays: 2nd, 9th, 16th, 23rd
        self.assertTrue(rep.accepts_date(date(2026, 2, 2)))    # week 0
        self.assertFalse(rep.accepts_date(date(2026, 2, 9)))   # week 1
        self.assertFalse(rep.accepts_date(date(2026, 2, 16)))  # week 2
        self.assertFalse(rep.accepts_date(date(2026, 2, 23)))  # week 3

    def test_second_week_only(self):
        rep = WeekdayRepetition(Weekdays.Monday, [1])
        self.assertFalse(rep.accepts_date(date(2026, 2, 2)))
        self.assertTrue(rep.accepts_date(date(2026, 2, 9)))
        self.assertFalse(rep.accepts_date(date(2026, 2, 16)))
        self.assertFalse(rep.accepts_date(date(2026, 2, 23)))

    def test_multiple_allowed_weeks(self):
        rep = WeekdayRepetition(Weekdays.Monday, [0, 2])
        self.assertTrue(rep.accepts_date(date(2026, 2, 2)))    # week 0
        self.assertFalse(rep.accepts_date(date(2026, 2, 9)))   # week 1
        self.assertTrue(rep.accepts_date(date(2026, 2, 16)))   # week 2
        self.assertFalse(rep.accepts_date(date(2026, 2, 23)))  # week 3

    def test_allowed_weeks_wrong_weekday_rejected(self):
        rep = WeekdayRepetition(Weekdays.Monday, [0])
        # Tuesday in week 0 should still be rejected
        self.assertFalse(rep.accepts_date(date(2026, 2, 3)))

    def test_allowed_weeks_with_month_having_five_occurrences(self):
        # March 2026 has 5 Sundays: 1, 8, 15, 22, 29
        rep = WeekdayRepetition(Weekdays.Sunday, [4])
        self.assertFalse(rep.accepts_date(date(2026, 3, 1)))
        self.assertFalse(rep.accepts_date(date(2026, 3, 8)))
        self.assertFalse(rep.accepts_date(date(2026, 3, 15)))
        self.assertFalse(rep.accepts_date(date(2026, 3, 22)))
        self.assertTrue(rep.accepts_date(date(2026, 3, 29)))


class WeekdayRepetitionGetAcceptableDatesTestCase(TestCase):
    def test_get_acceptable_dates_basic(self):
        rep = WeekdayRepetition(Weekdays.Wednesday, None)
        begin = datetime(2026, 2, 1)
        end = datetime(2026, 2, 28)
        dates = list(rep.get_acceptable_dates(begin, end))
        expected = [date(2026, 2, 4), date(2026, 2, 11), date(2026, 2, 18), date(2026, 2, 25)]
        self.assertEqual(expected, dates)

    def test_get_acceptable_dates_with_allowed_weeks(self):
        rep = WeekdayRepetition(Weekdays.Wednesday, [0, 2])
        begin = datetime(2026, 2, 1)
        end = datetime(2026, 2, 28)
        dates = list(rep.get_acceptable_dates(begin, end))
        expected = [date(2026, 2, 4), date(2026, 2, 18)]
        self.assertEqual(expected, dates)

    def test_get_acceptable_dates_empty_range(self):
        rep = WeekdayRepetition(Weekdays.Monday, None)
        # Range contains only Tuesday Feb 3
        begin = datetime(2026, 2, 3, 0, 0, 0)
        end = datetime(2026, 2, 3, 23, 59, 59)
        dates = list(rep.get_acceptable_dates(begin, end))
        self.assertEqual([], dates)

    def test_get_acceptable_dates_multiple_days(self):
        rep = WeekdayRepetition([Weekdays.Monday, Weekdays.Friday], None)
        begin = datetime(2026, 2, 1)
        end = datetime(2026, 2, 14)
        dates = list(rep.get_acceptable_dates(begin, end))
        expected = [date(2026, 2, 2), date(2026, 2, 6), date(2026, 2, 9), date(2026, 2, 13)]
        self.assertEqual(expected, dates)
