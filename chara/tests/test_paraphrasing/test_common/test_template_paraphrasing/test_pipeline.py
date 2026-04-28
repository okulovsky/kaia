from chara.paraphrasing.common.template_paraphrasing import *
from chara.common import CharaApis, CaseCache
from chara.common.tools.llm import PromptTaskBuilder
from grammatron import Template, CardinalDub
from unittest import TestCase
from brainbox.deciders import Collector
from brainbox.framework import ISelfManagingDecider
from brainbox import BrainBox
from foundation_kaia.misc import Loc
from dataclasses import dataclass

class OllamaMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt):
        return "* I set the timer for {duration} minutes\n* Your timer will elapse in {duration} minutes"


def f(case):
    return ""

class PipelineTestCase(TestCase):
    def test_pipeline(self):
        template = Template(f"The timer is set for {CardinalDub().as_variable('duration')} minutes")
        parsed_template = ParsedTemplate.parse(template)
        self.assertEqual(1, len(parsed_template))
        case = ParsedTemplateParaphraseCase(TemplateParaphraseCase(template, 'en'), parsed_template[0])
        with Loc.create_test_folder() as folder:
            with BrainBox.Api.serverless_test([OllamaMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                cache = CaseCache(folder)
                pipe = TemplateParaphrasePipeline(
                    PromptTaskBuilder('mistral', f),
                )
                pipe(cache, [case])

            result = cache.read_result()
            print(result)
            self.assertEqual(
                'I set the timer for five minutes',
                result[0].template.to_str(5)
            )
            self.assertEqual(
                'Your timer will elapse in six minutes',
                result[1].template.to_str(6)
            )
