from development.paraphrasing.paraphrase_info import ParaphraseInfo
from development.paraphrasing.paraphrase_case import ParaphraseCase
from eaglesong.templates import *
from avatar import Character, World
from foundation_kaia.prompters import Prompter
from unittest import TestCase
from pprint import pprint

char_1 = Character('Alice', Character.Gender.Feminine, 'Alice is Alice.')
char_2 = Character('Bob', Character.Gender.Masculine, 'Bob is Bob.')
relation = Prompter(f"{World.character} and {World.user} are friends.")

start = Template("Do something!")

def run(template):
    info = ParaphraseInfo.parse_from_template(template)
    if len(info) != 1:
        raise ValueError("Exactly one info is expected")
    case = ParaphraseCase(info[0], char_1, char_2, relation)
    template = ParaphraseCase.get_paraphrase_template()
    result = template(case)
    print(result)
    return result


class TemplateToParaphraseTestCase(TestCase):
    def test_simple(self):
        s = run(Template(f"Yes"))
        self.assertIn('Yes', s)

    def test_with_variable(self):
        s = run(Template(f"The answer is {CardinalDub(10).as_variable('variable')}"))
        self.assertIn('{variable}', s)
        self.assertIn('You need to preserve all the placeholders', s)
        self.assertNotIn('variable:', s) #because there is no description

    def test_with_variable_and_description(self):
        v = TemplateVariable("variable", CardinalDub(), "my description")
        s = run(Template(f"The answer is {v}"))
        self.assertIn('variable: my description', s)


    def test_with_variable_and_plural(self):
        s = run(Template(f"The answer is {CardinalDub(10).as_variable('variable')} {PluralAgreement('variable').as_variable()}"))
        self.assertIn('Values in square brackets', s)

    def test_with_context(self):
        t = Template(f"Yes").context(f'{World.character} agrees with {World.user}')
        s = run(t)
        self.assertIn('# Context', s)
        self.assertIn('The circumstances are following: Alice agrees with Bob', s)

    def test_with_reply(self):
        s = run(Template("Yes").context(reply_to=start))
        self.assertIn('The reply is a response for the following utterances from user:', s)
        self.assertIn('* Do something!', s)

    def test_with_reply_details(self):
        s = run(Template("No").context(reply_to=start, reply_details=f'{World.character} disagrees with {World.user}'))
        self.assertIn('The reply needs to express the following: Alice disagrees with Bob', s)


    def test_restoration(self):
        template = Template(f"The answer is {CardinalDub(10).as_variable('variable')} {PluralAgreement('variable').as_variable()}")
        info = ParaphraseInfo.parse_from_template(template)[0]
        s = "It's {variable} [variable|variables]! That's the answer"
        new_template = info.restore_template(s)
        self.assertEqual("It's one variable! That's the answer", new_template.to_str(dict(variable=1)))
        self.assertEqual("It's two variables! That's the answer", new_template.to_str(dict(variable=2)))


