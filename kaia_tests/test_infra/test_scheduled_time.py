from unittest import TestCase
from kaia.infra import *
from datetime import time, datetime, timedelta

class EventTimeTestCase(TestCase):
    def test_event_time(self):
        event = ScheduledTime(
            time(10,0,0),
        )
        self.assertTrue(event.intersects_with_interval(datetime(2020,1,1,9), datetime(2020,1,1,11)))
        self.assertTrue(event.intersects_with_interval(datetime(2020, 1, 1, 9), datetime(2020, 1, 1, 10)))
        self.assertTrue(event.intersects_with_interval(datetime(2020, 1, 1, 10), datetime(2020, 1, 1, 11)))
        self.assertTrue(event.intersects_with_interval(datetime(2020, 1, 2, 9), datetime(2020, 1, 2, 11)))

    def test_event_day(self):
        event = ScheduledTime(
            time(10, 0, 0),
            repetition=WeekdayRepetition([Weekdays.Monday, Weekdays.Thursday])
        )
        dt = datetime(2020,1,1,9)
        for i, result in enumerate([False, True, False, False, False, True, False]):
            with self.subTest(f'Shift {i}'):
                self.assertEqual(
                    result,
                    event.intersects_with_interval(dt+timedelta(days=i), dt+timedelta(days=i, hours=2))
                )

    def test_event_with_duration(self):
        event = ScheduledTime(
            time(10,0,0),
            duration = timedelta(hours = 2)
        )
        self.assertTrue(event.intersects_with_interval(datetime(2020,1,1,9), datetime(2020,1,1,10)))
        self.assertTrue(event.intersects_with_interval(datetime(2020, 1, 1, 12), datetime(2020, 1, 1, 13)))
        self.assertTrue(event.intersects_with_interval(datetime(2020,1,1,9), datetime(2020,1,1,11)))
        self.assertTrue(event.intersects_with_interval(datetime(2020, 1, 1, 11), datetime(2020, 1, 1, 13)))

    def test_error_on_wrong_interval(self):
        event = ScheduledTime(
            time(10, 0, 0),
        )
        self.assertRaises(
            ValueError,
            lambda: event.intersects_with_interval(datetime(2020, 1, 1,11), datetime(2020, 1, 1, 9))
        )







