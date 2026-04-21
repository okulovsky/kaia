from chara.common import CharaApis
from chara.common.tools.llm import PromptTaskBuilder
from chara.paraphrasing.basic_pipelines.options_expanding import OptionExpandingPipeline, OptionExpandingCaseManager, OptionExpandingCache
from unittest import TestCase
from grammatron import Template, OptionsDub
from foundation_kaia.misc import Loc
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Collector


class OllamaMock(ISelfManagingDecider):
    def __init__(self):
        self.call_count = 0

    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt):
        if self.call_count != 0:
            raise ValueError("Should be called once")
        self.call_count += 1
        if prompt == 'fruit':
            return "* mango\n* kiwi"
        raise ValueError(f"Unexpected prompt: {prompt}")


def f(case):
    return str(case.variable_name)


class TestOptionExpandingPipeline(TestCase):
    def test_options_expanding_pipeline(self):
        fruit_dub = OptionsDub(['banana', 'orange']).as_variable('fruit')
        fruit_dub_1 = OptionsDub(['banana', 'orange']).as_variable('fruit')
        templates = [
            Template(f"We need to buy {fruit_dub}"),
            Template(f"You ordered {fruit_dub_1}"),
        ]
        manager = OptionExpandingCaseManager(templates)

        with Loc.create_test_folder() as folder:
            with BrainBox.Api.serverless_test([OllamaMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                cache = OptionExpandingCache(folder)
                pipe = OptionExpandingPipeline(PromptTaskBuilder("test", f))
                pipe(cache, manager.prepare())
                result = cache.read_result()

        print(result)
        templates = manager.apply(result)
        self.assertEqual("We need to buy kiwi", templates[0].to_str("kiwi"))
        with self.assertRaises(Exception):
            templates[0].to_str("lemon")

        self.assertEqual("You ordered mango", templates[1].to_str("mango"))

