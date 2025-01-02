from kaia.dub import Template, FieldBinding, Address
from unittest import TestCase

USER = FieldBinding(Address('user'))
CHARACTER = FieldBinding(Address('character'))
USER_LAST_NAME = FieldBinding(Address('user','last_name'))

class TemplateTestCase(TestCase):
    def test_predefined_field(self):
        s = f'{USER}'
        self.assertTrue(s.startswith("<<<"))
        self.assertTrue(s.endswith(">>>"))
        print(s)

    def test_template_with_fields(self):
        t = Template(f'{USER} and {CHARACTER}')
        self.assertEqual(
            'A and B',
            t(user='A', character='B').to_str()
        )

    def test_template_with_excess_fields_fails(self):
        t = Template(f'{USER} and {CHARACTER}')
        self.assertRaises(Exception, lambda: t(user='A', character='B', test='C').to_str())


    def test_template_with_excess_fields_fails_non_restrictive(self):
        t = Template.free(f'{USER} and {CHARACTER}')
        self.assertEqual(
            'A and B',
            t(user='A', character='B', test='C').to_str()
        )

    def test_template_free(self):
        t = Template.free('{user} and {character}')
        self.assertEqual('A and B', t(user='A', character='B', test='C').to_str())

    def test_template_with_nested_binding(self):
        t = Template.free(f'{USER_LAST_NAME}')
        self.assertEqual('Test', t(user=dict(last_name='Test')).to_str())
