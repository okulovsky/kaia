from kaia.kaia.translators import ExpectedTemplatesTranslator, ExpectedTemplatesListenPayload
from eaglesong import Scenario, Listen, Automaton, Return
from unittest import TestCase
from kaia.dub import *

class Templates(TemplatesCollection):
    yes = Template("Yes")
    no = Template("No").as_input('Negative')
    cancel = Template("Cancel")


def f():
    while True:
        input = yield
        yield input
        yield Listen().store(ExpectedTemplatesListenPayload(Templates.yes, Templates.no))

def S():
    return Scenario(
        lambda: Automaton(ExpectedTemplatesTranslator(f), None),
    )

class ExpectedTemplatesTestCase(TestCase):
    def test_expected_templates(self):
        (
            S()
            .send(Templates.yes())
            .check(Templates.yes())
            .send(Templates.no())
            .check(Templates.no())
            .send(Templates.cancel())
            .check("Unexpected input. Expected: yes, Negative")
            .validate()
        )


