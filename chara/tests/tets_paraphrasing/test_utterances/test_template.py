from chara.paraphrasing.utterances import JinjaModel, ParaphrasingPrompter
from chara.paraphrasing.common import ParaphraseCase, ParsedTemplate
from grammatron import *
from avatar.daemon import Character, World
from foundation_kaia.prompters import Prompter
from unittest import TestCase

char_1 = Character('Alice', Character.Gender.Feminine, 'Alice is Alice.')
char_2 = Character('Bob', Character.Gender.Masculine, 'Bob is Bob.')

start = Template("Do something!")

def run(template):
    parsed = ParsedTemplate.parse(template)
    case = ParaphraseCase(parsed[0], 'en', char_1, char_2)
    result = ParaphrasingPrompter()(case)
    print(result)
    return result


class TemplateToParaphraseTestCase(TestCase):
    def test_simple(self):
        s = run(Template(f"Yes"))
        self.assertIn('* Yes', s)

    def test_with_variable(self):
        s = run(Template(f"The answer is {CardinalDub(10).as_variable('variable')}"))
        self.assertIn('Where:', s)
        self.assertIn('* {variable}.  Variable `variable`.', s)

    def test_with_variable_and_description(self):
        v = VariableDub("variable", CardinalDub(), "my description")
        s = run(Template(f"The answer is {v}"))
        self.assertIn('* {variable}.  Variable `variable`: my description.', s)


    def test_with_variable_and_plural(self):
        s = run(Template(f"The answer is {PluralAgreement(CardinalDub(10).as_variable('count'), 'variable')}"))

        self.assertIn('* {count/variable}. Variable `count`. Then, word `variable` is added in a grammatically correct form.', s)

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

