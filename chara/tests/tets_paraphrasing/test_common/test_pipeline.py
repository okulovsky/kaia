from chara.paraphrasing.common import *
from chara.common import CharaApis
from grammatron import Template, CardinalDub
from unittest import TestCase
from brainbox.deciders import Mock, Collector
from brainbox import BrainBox
from foundation_kaia.misc import Loc

class OllamaMock(Mock):
    def __init__(self):
        super().__init__("Ollama")

    def question(self, prompt: str, system_prompt):
        return "* I set the timer for {duration} minutes\n* Your timer will elapse in {duration} minutes"


def f(case: ParaphraseCase):
    return case.template.sequences[0].representation

class PipelineTestCase(TestCase):
    def test_pipeline(self):
        template = Template(f"The timer is set for {CardinalDub().as_variable('duration')} minutes")
        parsed_template = ParsedTemplate.parse(template)
        self.assertEqual(1, len(parsed_template))
        case = ParaphraseCase(parsed_template[0])
        with Loc.create_test_folder() as folder:
            with BrainBox.Api.Test([OllamaMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                cache = ParaphraseCache(folder)
                pipe = ParaphrasePipeline(
                    PromptTaskBuilder(f, 'mistral'),
                )
                pipe(cache, [case])

            result = cache.read_result()
            self.assertEqual(
                'I set the timer for five minutes',
                result[0].template.to_str(5)
            )
            self.assertEqual(
                'Your timer will elapse in six minutes',
                result[1].template.to_str(6)
            )
