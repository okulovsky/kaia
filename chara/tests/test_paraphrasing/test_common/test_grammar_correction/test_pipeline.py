from chara.paraphrasing.common.grammar_correction import *
from chara.common import CharaApis, CaseCache
from chara.common.tools.llm import PromptTaskBuilder
from grammatron import Template, CardinalDub, OptionsDub, PluralAgreement
from unittest import TestCase
from brainbox.deciders import Collector
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
                "{amount+fruit}" : {
                    "падеж": "Винительный",
                }
            }
        }
        return json.dumps(reply)


class GrammarCorrectiomPipelineTestCase(TestCase):
    def test_grammar_correction_pipeline(self):
        options = OptionsDub(['банан', 'яблоко', 'груша']).as_variable('fruit')
        template = Template(ru=f"Я съел {PluralAgreement(CardinalDub().as_variable('amount'), options)}")
        manager = GrammarCorrectionCaseManager([template])

        with Loc.create_test_folder() as folder:
            with BrainBox.Api.serverless_test([OllamaMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                cache = CaseCache(folder)
                pipe = GrammarCorrectionPipeline(PromptTaskBuilder('mistral'))
                cases = manager.prepare()
                pipe(cache, cases)
                result = cache.read_result()

        print(result[0].grammar_reply)
        templates = manager.apply(result)
        self.assertEqual(
            "Я съел одну грушу",
            templates[0].to_str(dict(fruit='груша', amount=1))
        )
