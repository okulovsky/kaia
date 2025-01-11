from kaia.dub import DictDub, Template
from unittest import TestCase

class DictDubTestCase(TestCase):
    def test_dict_dub_with_several_values(self):
        t = Template(
            "{value}",
            value = DictDub(dict(option_1 = 'A', option_2 = ['X', 'Y']))
        ).with_name('X')
        self.assertDictEqual(dict(value = 'option_1'), t.parse('A'))
        self.assertDictEqual(dict(value = 'option_2'), t.parse('X'))
        self.assertDictEqual(dict(value = 'option_2'), t.parse('Y'))
        self.assertEqual('A', t.to_str(dict(value='option_1')))
        self.assertEqual('X', t.to_str(dict(value='option_2')))

