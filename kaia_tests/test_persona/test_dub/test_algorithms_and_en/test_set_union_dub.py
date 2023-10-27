from kaia.persona.dub.languages.en import SetUnionDub, DictDub, Template
from unittest import TestCase
from enum import Enum



class SetUnionDubTestCase(TestCase):
    def test_parse(self):
        template = Template(
            '{dub}',
            dub = SetUnionDub(
            DictDub({1: 'one', 2:'two'}),
            DictDub({3: 'three', 4: 'four'})
        ))
        self.assertEqual('two', template.to_str(dict(dub=2)))
        self.assertEqual('three', template.to_str(dict(dub=3)))
        self.assertDictEqual(dict(dub=4), template.parse('four'))

    def test_ambigous_parse(self):
        template = Template(
            '{dub}',
            dub = SetUnionDub(
            DictDub({1: 'one'}),
            DictDub({3: 'one'})
        ))
        self.assertRaises(ValueError, lambda: template.parse('one'))

    def test_ambigous_tostr(self):
        template = Template(
            '{dub}',
            dub = SetUnionDub(
            DictDub({1: 'one'}),
            DictDub({1: 'first'})
        ))
        self.assertDictEqual(dict(dub=1), template.parse('one'))
        self.assertDictEqual(dict(dub=1), template.parse('first'))
        self.assertEqual('one', template.to_str(dict(dub=1)))
        self.assertEqual(('one', 'first'), template.to_all_strs(dict(dub=1)))


