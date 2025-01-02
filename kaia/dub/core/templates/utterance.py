from typing import *
from .template import Template
from eaglesong.core.testing.scenario import IAsserter
from unittest import TestCase

class Utterance(IAsserter):
    def __init__(self, template: Template, value: Any):
        self.template = template
        self._value = value
        self.confidence: float|None = None
        try:
            self.to_str()
        except Exception as ex:
            raise ValueError(
                "Can't create utterance: probably mistmatch between parameters and required fields\nTEMPLATES:\n"+
                "\n".join(self.template.string_templates)
                +"\nVALUE:\n"
                +str(value)
            ) from ex


    @property
    def value(self):
        return self._value

    def to_str(self):
        return self.template.to_str(self.value)


    def assertion(self, actual, test_case: TestCase):
        test_case.assertIsInstance(actual, Utterance)
        test_case.assertEqual(self.template.name, actual.template.name)
        test_case.assertDictEqual(self.value, actual.value)


    def get_field(self, name: str|None = None, default_value = None):
        if name is None:
            if len(self.value) == 1:
                return self.value[list(self.value)[0]]
            else:
                raise ValueError(f"Cannot extract a single value, several values are in the dict {self.value}")
        else:
            return self.value.get(name, default_value)


    def __str__(self):
        return '[Utterance] '+self.to_str()

    def __add__(self, another: 'Utterance'):
        from .utterance_sequence import UtterancesSequence
        return UtterancesSequence(self, another)

    @staticmethod
    def from_string(s: str):
        return Utterance(
            Template(s).with_name('On-the-fly template '+s),
            {}
        )
