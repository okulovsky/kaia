from unittest import TestCase
from kaia.eaglesong.arch import *


def linear_method(c):
    yield 'A'
    yield c() * 2



class TestAutomaton(TestCase):
    def setUp(self):
        self.aut = Automaton(FunctionalSubroutine(linear_method))

    def test_reply(self):
        self.assertEqual('A',self.aut.process(''))

    def test_mind_input(self):
        self.aut.process('')
        self.assertEqual(4,self.aut.process(2))

    def test_terminate(self):
        self.aut.process('')
        self.aut.process(1)
        self.assertTrue(isinstance(self.aut.process(''),Return))



