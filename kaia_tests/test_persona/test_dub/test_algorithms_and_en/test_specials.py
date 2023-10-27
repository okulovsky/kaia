from kaia.persona.dub.languages.en import *
from unittest import TestCase
from datetime import datetime

class DateDubTestCase(TestCase):
    def test_special_case(self):
        template = Template('{value}', value=TimedeltaDub())
