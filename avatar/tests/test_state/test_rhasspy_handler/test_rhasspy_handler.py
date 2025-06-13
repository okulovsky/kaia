from eaglesong.templates import OptionsDub, Template
from unittest import TestCase
from avatar.state import RhasspyHandler

class DictDubTestCase(TestCase):
    def test_dict_dub_with_several_values(self):
        var = Template.Variable(
            "value",
            OptionsDub(dict(A = 'option_1', X='option_2', Y='option_3'))
        )
        template = Template(f"{var}").with_name('X')

        handler = RhasspyHandler([template])
        self.assertEqual('[X]\nvalue = a|x|y\n<value>{value}', handler.ini_file)
