from chara.paraphrasing.basic_pipelines.template_paraphrasing import ParsedTemplate
from grammatron import Template, CardinalDub, PluralAgreement, OptionsDub
from unittest import TestCase

class TestParsedTemplate(TestCase):
    def test_no_variable(self):
        t = Template("Success!")
        ps = ParsedTemplate.parse(t)
        self.assertEqual(1, len(ps))
        p = ps[0]
        self.assertEqual('', p.variables_tag)
        self.assertEqual((), p.variables)

        self.assertEqual(0, len(p.alternatives))
        self.assertEqual("Success!", p.representation)

    def test_one_variable(self):
        t = Template(f"The amount is {CardinalDub().as_variable('test')}")
        ps = ParsedTemplate.parse(t)
        self.assertEqual(1, len(ps))
        p = ps[0]
        self.assertEqual('test', p.variables_tag)
        self.assertEqual(1, len(p.variables))
        self.assertEqual('test', p.variables[0].name)

        self.assertEqual(0, len(p.alternatives))
        self.assertEqual("The amount is {test}", p.representation)

    def test_plural_agreement_with_constant(self):
        t = Template(f"There are {PluralAgreement(CardinalDub().as_variable('test'), 'banana')}")
        ps = ParsedTemplate.parse(t)
        self.assertEqual(1, len(ps))
        p = ps[0]
        self.assertEqual('test', p.variables_tag)
        self.assertEqual(1, len(p.variables))
        self.assertEqual('test', p.variables[0].name)

        self.assertEqual(0, len(p.alternatives))
        self.assertEqual("There are {test+banana}", p.representation)

    def test_plural_agreement_with_variable(self):
        options = OptionsDub(['banana','orange'])
        t = Template(f"There are {PluralAgreement(CardinalDub().as_variable('amount'), options.as_variable('fruit'))}")
        ps = ParsedTemplate.parse(t)
        self.assertEqual(1, len(ps))
        p = ps[0]
        self.assertEqual('amount,fruit', p.variables_tag)
        self.assertEqual(2, len(p.variables))
        self.assertEqual('amount', p.variables[0].name)
        self.assertEqual('fruit', p.variables[1].name)

        self.assertEqual(0, len(p.alternatives))
        self.assertEqual("There are {amount+fruit}", p.representation)


    def test_multicase(self):
        msg = CardinalDub().as_variable('messages')
        unread = CardinalDub().as_variable('unread')
        t = Template(
            f"Amount of messages: {msg}",
            f"Available messages: {msg}",
            f"Messages: {msg}, unread: {unread}"
        )
        ps = ParsedTemplate.parse(t)
        self.assertEqual(2, len(ps))

        self.assertEqual('messages', ps[0].variables_tag)
        self.assertEqual('messages,unread', ps[1].variables_tag)

        self.assertEqual(1, len(ps[0].alternatives))
        self.assertEqual(0, len(ps[1].alternatives))





