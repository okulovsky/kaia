from typing import Any
from unittest import TestCase
from pprint import pprint

_tc = TestCase()
_tc.maxDiff = None

class ControlValue:
    def __init__(self, value: Any):
        self.value = value

    def mddoc_validate_control_value(self, actual):
        if callable(actual):
            _tc.assertTrue(actual())
            print("custom check passed")
            pprint(self.value)
        else:
            _tc.assertEqual(self.value, actual)
            pprint(actual)



    @staticmethod
    def mddoc_define_control_value(value):
        return ControlValue(value)

