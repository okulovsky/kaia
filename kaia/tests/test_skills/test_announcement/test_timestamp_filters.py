from unittest import TestCase
from datetime import datetime, timedelta, date
from kaia.skills.announcement_skill.use_cases.timestamp_filters import Calendar, Weekdays, Hours, RandomTime


# 2024-01-01 is a Monday
MONDAY_WEEK1 = datetime(2024, 1, 1, 12, 0)   # Monday, week 1 of month  (day 1)
SATURDAY_WEEK1 = datetime(2024, 1, 6, 12, 0)  # Saturday, week 1 of month (day 6)
SUNDAY_WEEK1 = datetime(2024, 1, 7, 12, 0)    # Sunday, week 1 of month  (day 7)
MONDAY_WEEK2 = datetime(2024, 1, 8, 12, 0)    # Monday, week 2 of month  (day 8)
MONDAY_WEEK3 = datetime(2024, 1, 15, 12, 0)   # Monday, week 3 of month  (day 15)
MONDAY_WEEK4 = datetime(2024, 1, 22, 12, 0)   # Monday, week 4 of month  (day 22)
MONDAY_WEEK5 = datetime(2024, 1, 29, 12, 0)   # Monday, week 5 of month  (day 29)


class TestCalendarWeekdays(TestCase):
    def test_no_filter_always_passes(self):
        cal = Calendar()
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK1))
        self.assertTrue(cal.should_announce_at_datetime(SATURDAY_WEEK1))

    def test_weekday_filter_passes_matching_day(self):
        cal = Calendar(weekdays=[Weekdays.Monday])
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK1))

    def test_weekday_filter_blocks_non_matching_day(self):
        cal = Calendar(weekdays=[Weekdays.Monday])
        self.assertFalse(cal.should_announce_at_datetime(SATURDAY_WEEK1))

    def test_multiple_weekdays(self):
        cal = Calendar(weekdays=[Weekdays.Monday, Weekdays.Saturday])
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK1))
        self.assertTrue(cal.should_announce_at_datetime(SATURDAY_WEEK1))
        self.assertFalse(cal.should_announce_at_datetime(SUNDAY_WEEK1))

    def test_workdays_passes_weekday(self):
        cal = Calendar().workdays()
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK1))

    def test_workdays_blocks_weekend(self):
        cal = Calendar().workdays()
        self.assertFalse(cal.should_announce_at_datetime(SATURDAY_WEEK1))
        self.assertFalse(cal.should_announce_at_datetime(SUNDAY_WEEK1))

    def test_weekend_passes_saturday_and_sunday(self):
        cal = Calendar().weekend()
        self.assertTrue(cal.should_announce_at_datetime(SATURDAY_WEEK1))
        self.assertTrue(cal.should_announce_at_datetime(SUNDAY_WEEK1))

    def test_weekend_blocks_weekday(self):
        cal = Calendar().weekend()
        self.assertFalse(cal.should_announce_at_datetime(MONDAY_WEEK1))


class TestCalendarMonthIndex(TestCase):
    def test_month_index_filter_passes_correct_week(self):
        cal = Calendar(month_indices=[1])
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK1))

    def test_month_index_filter_blocks_wrong_week(self):
        cal = Calendar(month_indices=[1])
        self.assertFalse(cal.should_announce_at_datetime(MONDAY_WEEK2))

    def test_even_weeks_passes_week2_and_week4(self):
        cal = Calendar().even_weeks()
        self.assertFalse(cal.should_announce_at_datetime(MONDAY_WEEK1))
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK2))
        self.assertFalse(cal.should_announce_at_datetime(MONDAY_WEEK3))
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK4))
        self.assertFalse(cal.should_announce_at_datetime(MONDAY_WEEK5))

    def test_odd_weeks_passes_week1_week3_week5(self):
        cal = Calendar().odd_weeks()
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK1))
        self.assertFalse(cal.should_announce_at_datetime(MONDAY_WEEK2))
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK3))
        self.assertFalse(cal.should_announce_at_datetime(MONDAY_WEEK4))
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK5))

    def test_combined_weekday_and_month_index(self):
        cal = Calendar(weekdays=[Weekdays.Monday], month_indices=[2])
        self.assertFalse(cal.should_announce_at_datetime(MONDAY_WEEK1))   # right weekday, wrong week
        self.assertTrue(cal.should_announce_at_datetime(MONDAY_WEEK2))    # right weekday, right week
        self.assertFalse(cal.should_announce_at_datetime(SATURDAY_WEEK1)) # wrong weekday, wrong week


class TestHours(TestCase):
    def test_hour_within_range(self):
        f = Hours(from_hour=10, to_hour=18)
        self.assertTrue(f.should_announce_at_datetime(datetime(2024, 1, 1, 12, 0)))

    def test_hour_at_lower_boundary(self):
        f = Hours(from_hour=10, to_hour=18)
        self.assertTrue(f.should_announce_at_datetime(datetime(2024, 1, 1, 10, 0)))

    def test_hour_at_upper_boundary(self):
        f = Hours(from_hour=10, to_hour=18)
        self.assertTrue(f.should_announce_at_datetime(datetime(2024, 1, 1, 18, 0)))
        self.assertFalse(f.should_announce_at_datetime(datetime(2024, 1, 1, 18, 30)))

    def test_hour_below_range(self):
        f = Hours(from_hour=10, to_hour=18)
        self.assertFalse(f.should_announce_at_datetime(datetime(2024, 1, 1, 9, 59)))

    def test_hour_above_range(self):
        f = Hours(from_hour=10, to_hour=18)
        self.assertFalse(f.should_announce_at_datetime(datetime(2024, 1, 1, 19, 0)))


class TestRandomTime(TestCase):
    def test_window_is_cached_per_date(self):
        f = RandomTime(from_hour=10, to_hour=12, percentage=0.5)
        dt = datetime(2024, 1, 1, 11, 0)
        result1 = f.should_announce_at_datetime(dt)
        result2 = f.should_announce_at_datetime(dt)
        self.assertEqual(result1, result2)

    def test_separate_cache_entry_per_date(self):
        f = RandomTime(from_hour=10, to_hour=12, percentage=0.5)
        f.should_announce_at_datetime(datetime(2024, 1, 1, 11, 0))
        f.should_announce_at_datetime(datetime(2024, 1, 2, 11, 0))
        self.assertEqual(2, len(f._date_to_choosen_time))

    def test_timestamp_at_window_start_passes(self):
        f = RandomTime(from_hour=10, to_hour=12, percentage=0.5)
        test_date = date(2024, 1, 1)
        f.should_announce_at_datetime(datetime(2024, 1, 1, 11, 0))
        offset = f._date_to_choosen_time[test_date]
        begin = datetime(2024, 1, 1, 10, 0) + timedelta(seconds=offset)
        self.assertTrue(f.should_announce_at_datetime(begin))

    def test_timestamp_before_window_fails(self):
        f = RandomTime(from_hour=10, to_hour=12, percentage=0.5)
        test_date = date(2024, 1, 1)
        f.should_announce_at_datetime(datetime(2024, 1, 1, 11, 0))
        offset = f._date_to_choosen_time[test_date]
        begin = datetime(2024, 1, 1, 10, 0) + timedelta(seconds=offset)
        self.assertFalse(f.should_announce_at_datetime(begin - timedelta(seconds=1)))

    def test_timestamp_at_window_end_passes(self):
        f = RandomTime(from_hour=10, to_hour=12, percentage=0.5)
        test_date = date(2024, 1, 1)
        f.should_announce_at_datetime(datetime(2024, 1, 1, 11, 0))
        offset = f._date_to_choosen_time[test_date]
        begin = datetime(2024, 1, 1, 10, 0) + timedelta(seconds=offset)
        end = begin + timedelta(seconds=f._choosen_span_in_seconds)
        self.assertTrue(f.should_announce_at_datetime(end))

    def test_timestamp_after_window_fails(self):
        f = RandomTime(from_hour=10, to_hour=12, percentage=0.5)
        test_date = date(2024, 1, 1)
        f.should_announce_at_datetime(datetime(2024, 1, 1, 11, 0))
        offset = f._date_to_choosen_time[test_date]
        begin = datetime(2024, 1, 1, 10, 0) + timedelta(seconds=offset)
        end = begin + timedelta(seconds=f._choosen_span_in_seconds)
        self.assertFalse(f.should_announce_at_datetime(end + timedelta(seconds=1)))
