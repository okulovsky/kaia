from grammatron.tests.common import *
from datetime import date

class DateDubTestCase(TestCase):
    def test_simple(self):
        dub = DateDub()
        self.assertEqual('January, sixth, twenty-fourth', dub.to_str(date(2024,1,6)))

    def test_date(self):
        dates = [date(2019+i, i+1, i+1) for i in range(12)]
        run_regex_integration_test(self,
            DateDub(),
            dates
        )