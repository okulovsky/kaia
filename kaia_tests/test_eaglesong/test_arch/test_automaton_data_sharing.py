from unittest import TestCase
from kaia.eaglesong.core.automaton import Automaton, ContextRequest, Return, Terminate


class T:
    def __init__(self):
        self.state = -1

    def run(self):
        self.state += 1
        yield self.state


class AutomatonDataSharingTestCase(TestCase):

    def test_full_sharing_scenario(self):
        shared = T()
        aut1 = Automaton(shared.run, None)
        aut2 = Automaton(shared.run, None)

        self.assertEqual(0, aut1.process(''))
        self.assertIsInstance(aut1.process(''), Return)
        self.assertEqual(1, aut1.process(''))
        self.assertEqual(2, aut2.process(''))

    def test_call_sharing(self):
        aut1 = Automaton(T().run, None)
        aut2 = Automaton(T().run, None)

        self.assertEqual(0, aut1.process(''))
        self.assertIsInstance(aut1.process(''), Return)
        self.assertEqual(1, aut1.process(''))
        self.assertEqual(0, aut2.process(''))

    def test_no_sharing(self):
        aut1 = Automaton(lambda: T().run(), None)
        aut2 = Automaton(lambda: T().run(), None)

        self.assertEqual(0, aut1.process(''))
        self.assertIsInstance(aut1.process(''), Return)
        self.assertEqual(0, aut1.process(''))
        self.assertEqual(0, aut2.process(''))


