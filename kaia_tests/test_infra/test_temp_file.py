from kaia.infra import Loc
from unittest import TestCase
from pathlib import Path

class TempFileTestCase(TestCase):
    def test_temp_file(self):
        with Loc.temp_file('test','txt') as temp:
            with open(temp, 'w') as wstream:
                wstream.write('test test')
            with open(temp,'r') as rstream:
                self.assertEqual('test test', rstream.read())
        self.assertFalse(temp.is_file())