from chara.paraphrasing.common import TemplateParaphrase, ParsedTemplate, Paraphrase
from chara.common import Chara, CaseCollection
from chara.common.tools.llm import PromptTaskBuilder
from grammatron import Template, CardinalDub
from unittest import TestCase
from brainbox.framework import ISelfManagingDecider
from brainbox import BrainBox
from foundation_kaia.misc import Loc


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
        case = Paraphrase.Case(template, 'en')
        case.parsed_template = parsed_template[0]

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = TemplateParaphrase.Pipeline(PromptTaskBuilder('mistral', f))
            with BrainBox.Api.serverless_test([OllamaMock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipe)(CaseCollection([case])).cases

        self.assertEqual(2, len(result))
        self.assertEqual('I set the timer for five minutes', result[0].resulting_template.to_str(5))
        self.assertEqual('Your timer will elapse in six minutes', result[1].resulting_template.to_str(6))
