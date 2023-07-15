import pandas as pd

from kaia.bro.sandbox import SimpleSpace
from unittest import TestCase

class SpaceTestCase(TestCase):
    def test_get_slots(self):
        space = SimpleSpace()
        slots = space.get_slots()
        self.assertEqual(['int_slot','string_slot'], [c.name for c in slots])

    def test_two_spaces(self):
        space1 = SimpleSpace()
        space2 = SimpleSpace()
        space1.int_slot._history = [1,2,3]
        self.assertListEqual([], space2.int_slot.history.to_list())




