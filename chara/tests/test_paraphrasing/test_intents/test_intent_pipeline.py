from unittest import TestCase
from brainbox import BrainBox
from brainbox.deciders import Mock, Ollama, Collector
from foundation_kaia.misc import Loc
from chara.common import CharaApis
from chara.paraphrasing.common.llm_tools import PromptTaskBuilder
from chara.paraphrasing.intents import (
    IntentCaseBuilder, IntentPrompter, IntentPipeline, IntentPipelineCache, IntentCase,
)
from kaia.skills.timer_skill import TimerIntents


class OllamaMock(Mock):
    def __init__(self):
        super().__init__('Ollama')

    def question(self, prompt: str, system_prompt=None):
        return "* Поставь таймер на {duration}\n* Включи таймер на {duration}"


class IntentPipelineTestCase(TestCase):
    def test_pipeline_with_mock(self):
        cases = IntentCaseBuilder(
            templates=list(TimerIntents.get_templates()),
            languages=('ru',),
        ).create_cases()

        builder = PromptTaskBuilder(prompter=IntentPrompter(), model='test-model')

        with Loc.create_test_folder() as folder:
            cache = IntentPipelineCache(folder)

            with BrainBox.Api.ServerlessTest([OllamaMock(), Collector()]) as service:
                CharaApis.brainbox_api = service
                IntentPipeline(builder)(cache, cases)

            results = list(cache.llm.read_cases_and_options())
            self.assertGreater(len(results), 0)
            case, paraphrase = results[0]
            self.assertIsInstance(case, IntentCase)
            self.assertIsInstance(paraphrase, str)
            self.assertGreater(len(paraphrase), 0)
