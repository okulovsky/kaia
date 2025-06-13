from unittest import TestCase

import click

from eaglesong.templates import Template, Utterance, UtterancesSequence

a = Template('a')
b = Template('b')

class AddTestCase(TestCase):
    def test_add_utterances(self):
        r = a.utter() + b.utter()
        self.assertIsInstance(r, UtterancesSequence)
        self.assertEqual(2, len(r.utterances))

    def test_add_3_utterances(self):
        r = a.utter() + b.utter() + a.utter()
        self.assertIsInstance(r, UtterancesSequence)
        self.assertEqual(3, len(r.utterances))

