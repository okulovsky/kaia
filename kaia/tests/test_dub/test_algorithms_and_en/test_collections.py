from typing import *
from kaia.dub.core import Template, Dub, TemplatesCollection
from unittest import TestCase


class MyIntents(TemplatesCollection):
    yes = Template('yes')
    no = Template('no')

class IntentsBaseTestCase(TestCase):
    def test_my_intents(self):
        self.assertIsInstance(MyIntents.yes, Template)
        self.assertTrue(MyIntents.yes.name.endswith('.MyIntents.yes'))
        self.assertEqual(2, len(MyIntents.get_templates()))