from kaia.avatar.dub.core import Template, ToStrDub, TemplatesCollection
from unittest import TestCase

class Replies(TemplatesCollection):
    test = Template(
        'A is {a}, B is {b}',
        'A is {a}',
        'B is {b}',
        'Alternative B is {b}',
        'Nothing',
        a = ToStrDub(),
        b = ToStrDub()
    )


class ProperOptionSelectionTestCase(TestCase):
    def check(self, *results, **kwargs):
        intent = Replies.get_templates()[0]
        s = intent.to_all_strs(kwargs)
        for i,v in enumerate(results):
            self.assertEquals(v, s[i])

    def test_both(self):
        self.check('A is 5, B is 6', a=5, b=6)

    def test_first(self):
        self.check('A is 5', a=5)

    def test_second_multiple(self):
        self.check('B is 6', 'Alternative B is 6', b=6)

    def test_nothing(self):
        self.check('Nothing')

    def test_none(self):
        self.check('A is 7', a=7, b=None)