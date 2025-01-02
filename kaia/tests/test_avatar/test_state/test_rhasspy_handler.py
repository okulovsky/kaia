from kaia.dub import DictDub, Template
from unittest import TestCase
from kaia.avatar.state import RhasspyHandler

class DictDubTestCase(TestCase):
    def test_dict_dub_with_several_values(self):
        t = Template(
            "{value}",
            value = DictDub(dict(option_1 = 'A', option_2 = ['X', 'Y']))
        ).with_name('X')

        handler = RhasspyHandler([t])
        self.assertEqual('[X]\n_value = A|X|Y\n<_value>{_value}', handler.ini_file)
