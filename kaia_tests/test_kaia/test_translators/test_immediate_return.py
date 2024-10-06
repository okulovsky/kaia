from kaia.kaia.translators import ImmediateStopListenPayload, ImmediateStopTranslator
from kaia.eaglesong import Scenario, Listen, Automaton, Return
from unittest import TestCase
from kaia.dub import *

class Intents:
    stop = Template("Stop")
    dont_stop = Template("Don't stop")

def f():
    while True:
        input = yield
        yield input
        yield Listen().store(ImmediateStopListenPayload(Intents.stop))

def S():
    return Scenario(
        lambda: Automaton(ImmediateStopTranslator(f), None),
    )

class ImmediateStopTranslatorTestCase(TestCase):
    def test_immediate_stop(self):
        (
            S()
            .send(Intents.dont_stop())
            .check(Intents.dont_stop())
            .send(Intents.stop())
            .check(Return)
            .validate()
        )