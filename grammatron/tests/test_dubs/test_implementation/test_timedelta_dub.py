from grammatron.tests.common import *
from datetime import timedelta

class TimeDeltaTestCase(TestCase):
    def test_tostr(self):
        v = timedelta(hours=2, minutes=12, seconds=3)
        self.assertEqual(
            'seven thousand, nine hundred and twenty-three seconds',
            TimedeltaDub(False, False, True).to_str(v)
        )

        self.assertEqual(
            'one hundred and thirty-two minutes',
            TimedeltaDub(False, True, False).to_str(v)
        )

        self.assertEqual(
            'one hundred and thirty-two minutes and three seconds',
            TimedeltaDub(False,True, True).to_str(v)
        )

        self.assertEqual(
            'two hours',
            TimedeltaDub(True, False, False).to_str(v)
        )

        self.assertRaises(Exception, lambda: TimedeltaDub(True, False, True))

        self.assertEqual('two hours and twelve minutes', TimedeltaDub(True, True, False).to_str(v))

        self.assertEqual('two hours, twelve minutes and three seconds', TimedeltaDub(True, True, True).to_str(v))

        self.assertEqual("five hours", TimedeltaDub().to_str(timedelta(hours=5)))

    def test_integral(self):
        run_regex_integration_test(
            self,
            TimedeltaDub(),
            [
                timedelta(seconds=3),
                timedelta(minutes=3, seconds=59),
                timedelta(minutes=5),
                timedelta(hours=4, seconds=3),
                timedelta(hours=7)
            ]
        )

