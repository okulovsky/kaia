from unittest import TestCase
from kaia.dub import Template, ToStrDub

class SimplestTemplateTestCase(TestCase):
    def test_simplest_template(self):
        t = Template("A is {A}", A=ToStrDub())
        print(t.to_str(dict(A='A')))