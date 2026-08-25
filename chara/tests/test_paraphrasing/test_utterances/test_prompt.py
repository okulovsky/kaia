from chara.paraphrasing.utterances import UtteranceParaphraseCase
from grammatron import *
from chara.common.descriptions import Character, World
from chara.paraphrasing.common import Paraphrase
from chara.paraphrasing.utterances.prompter import create_default_utterance_request
from chara.common.llm import BrainBoxLLMEngine, LLMSetup
from unittest import TestCase

char_1 = Character('Alice', Character.Gender.Feminine, 'Alice is Alice.')
char_2 = Character('Bob', Character.Gender.Masculine, 'Bob is Bob.')

start = Template("Do something!")

class TemplateToParaphraseTestCase(TestCase):
    def _check(self, template):
        case = UtteranceParaphraseCase(template, 'en', char_1, char_2)
        parsed_cases = Paraphrase([case]).prepare().cases
        self.assertEqual(1, len(parsed_cases))
        self.assertIsInstance(parsed_cases[0], UtteranceParaphraseCase)
        request = create_default_utterance_request(LLMSetup(BrainBoxLLMEngine(), ''))
        prompt = request.build_prompt(parsed_cases[0])
        print(prompt)
        return prompt



    def test_simple(self):
        s = self._check(Template(f"Yes"))
        self.assertIn('* Yes', s)

    def test_with_variable(self):
        s = self._check(Template(f"The answer is {CardinalDub(10).as_variable('variable')}"))
        self.assertIn('The command contains the following variables:', s)
        self.assertIn('* `{variable}`: Example:', s)

    def test_with_variable_and_description(self):
        v = VariableDub("variable", CardinalDub(), "my description")
        s = self._check(Template(f"The answer is {v}"))
        self.assertIn('* `{variable}`: my description. Example:', s)


    def test_with_variable_and_plural(self):
        s = self._check(Template(f"The answer is {PluralAgreement(CardinalDub(10).as_variable('count'), 'variable')}"))
        self.assertIn('* `{count+variable}`: A grammatically correct agreement of numeric variable `count` with the word "variable". Example:', s)

    def test_with_context(self):
        t = Template(f"Yes").context(f'{World.character} agrees with {World.user}')
        s = self._check(t)
        self.assertIn('# Context', s)
        self.assertIn('The circumstances are following: Alice agrees with Bob', s)

    def test_with_reply(self):
        s = self._check(Template("Yes").context(reply_to=start))
        self.assertIn('The reply is a response for the following utterances from user:', s)
        self.assertIn('* Do something!', s)

    def test_with_reply_details(self):
        s = self._check(Template("No").context(reply_to=start, reply_details=f'{World.character} disagrees with {World.user}'))
        self.assertIn('The reply needs to express the following: Alice disagrees with Bob', s)
