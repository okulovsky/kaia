from chara.paraphrasing.common import GrammarCorrection
from chara.common import Chara
from chara.common.tools.llm import PromptTaskBuilder
from grammatron import Template, CardinalDub, OptionsDub, PluralAgreement
from unittest import TestCase
from brainbox.framework import ISelfManagingDecider
from brainbox import BrainBox
from foundation_kaia.misc import Loc
import json


class OllamaMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt):
        reply = {
            "text": "...",
            "grammar": {
                "{amount+fruit}": {
                    "падеж": "Винительный",
                }
            }
        }
        return json.dumps(reply)


class GrammarCorrectionPipelineTestCase(TestCase):
    def test_grammar_correction_pipeline(self):
        options = OptionsDub(['банан', 'яблоко', 'груша']).as_variable('fruit')
        template = Template(ru=f"Я съел {PluralAgreement(CardinalDub().as_variable('amount'), options)}")
        manager = GrammarCorrection([template])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = GrammarCorrection.Pipeline(PromptTaskBuilder('mistral'))
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipe)(manager.prepare())

        cases = result.cases
        self.assertEqual(1, len(cases))
        print(cases[0].grammar_reply)
        templates = manager.apply(cases)
        self.assertEqual(
            "Я съел одну грушу",
            templates[0].to_str(dict(fruit='груша', amount=1))
        )
