from unittest import TestCase
from kaia.dub.core import Template

class TemplatesEqTestCase(TestCase):
    def test_eq_neq(self):
        t1 = Template().with_name('a')
        t2 = Template().with_name('a')
        t3 = Template().with_name('b')
        self.assertTrue(t1==t2)
        self.assertFalse(t1!=t2)
        self.assertFalse(t1==t3)
        self.assertTrue(t1!=t3)

    def test_no_name(self):
        t1 = Template()
        t2 = t1
        t3 = Template()
        self.assertTrue(t1 == t2)
        self.assertFalse(t1 != t2)
        self.assertFalse(t1 == t3)
        self.assertTrue(t1 != t3)
