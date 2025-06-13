from typing import *
from .template_base import TemplateBase
from eaglesong.core.testing.scenario import IAsserter
from unittest import TestCase

class Utterance(IAsserter):
    def __init__(self, template: TemplateBase, value: Any):
        self.template = template
        self._value = value
        self.confidence: float|None = None
        self.to_str()


    @property
    def value(self):
        return self._value

    def to_str(self):
        return self.template.to_str(self.value)

    def __str__(self):
        return f'[Utterance: {self.template.get_name()} {self.value}]'

    def __repr__(self):
        return self.__str__()


    def assertion(self, actual, test_case: TestCase):
        test_case.assertIsInstance(actual, Utterance)
        test_case.assertEqual(self.template.get_name(), actual.template.get_name())
        if isinstance(self.value, dict) != isinstance(actual.value, dict):
            raise ValueError(f"One is dictionary, another is not\n{actual.value}\n{self.value}")
        if isinstance(self.value, dict):
            test_case.assertDictEqual(self.value, actual.value)
        else:
            test_case.assertEqual(self.value, actual.value)


    def get_field(self, name: str|None = None, default_value = None):
        if name is None:
            if len(self.value) == 1:
                return self.value[list(self.value)[0]]
            else:
                raise ValueError(f"Cannot extract a single value, several values are in the dict {self.value}")
        else:
            return self.value.get(name, default_value)


    def __add__(self, another: 'Utterance'):
        from .utterance_sequence import UtterancesSequence
        return UtterancesSequence(self, another)
