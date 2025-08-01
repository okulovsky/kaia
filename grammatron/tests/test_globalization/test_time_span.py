from datetime import timedelta
from unittest import TestCase
from grammatron.tests.common import *


v = timedelta(hours=3, minutes=21, seconds=58)

class TimeDeltaDubTestCase(TestCase):
    def test_structure(self):
        t = TimedeltaDub()
        print(type(t.dispatch['en'].sequences[0]))

    def test_work(self):
        self.assertEqual('three hours, twenty-one minutes and fifty-eight seconds', TimedeltaDub().to_str(v))
        self.assertEqual('три часа, двадцать одна минута и пятьдесят восемь секунд', TimedeltaDub().to_str(v, DubParameters(language='ru')))



