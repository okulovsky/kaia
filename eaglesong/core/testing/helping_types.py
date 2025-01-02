from unittest import TestCase

class CheckType:
    def __init__(self, type):
        self.type = type

    def __call__(self, v, tc: TestCase):
        tc.assertIsInstance(v, self.type)


class CheckValue:
    def __init__(self, expected):
        self.expected = expected

    def __call__(self, v, tc: TestCase):
        tc.assertEqual(self.expected, v)


class Stash:
    def __init__(self, slot):
        self.slot = slot
        self.scenario = None

    def __call__(self, v, tc: TestCase):
        self.scenario.stashed_values[self.slot] = v