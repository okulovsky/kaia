from avatar.app import AvatarApi
from unittest import TestCase
from grammatron import Template
from chara.paraphrasing.utterances import UtteranceParaphraseCaseManager, UtteranceParaphrasePipeline
from chara.paraphrasing.common import Paraphrase
from chara.paraphrasing.utterances.prompter import setup_default_prompter
from chara.common import Chara
from chara.common.tools.llm import PromptTaskBuilder
from foundation_kaia.misc import Loc
from brainbox import BrainBox, ISelfManagingDecider


class Mock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt=None, options=None, num_predict=None):
        return "* Sure!\n* Yep!"


class UtterancePipelineTestCase(TestCase):
    def test_pipeline(self):
        builder = PromptTaskBuilder('test')
        setup_default_prompter(builder)
        settings = Paraphrase.Settings(
            paraphrase_task_builder=builder,
            enable_words_translation=False,
            grammar_correction_attempts=None,
            enable_options_expanding=False,
        )
        manager = UtteranceParaphraseCaseManager(
            [Template("yes"), Template("no")],
            target_languages=('en',)
        )
        pipe = UtteranceParaphrasePipeline(manager, settings, templates_in_batch=10, max_batch_iterations=1)

        with Loc.create_test_folder() as avatar_folder:
            with Loc.create_test_folder() as folder:
                Chara.start(folder)
                with AvatarApi.test(avatar_folder) as avatar_api:
                    Chara.Apis.avatar_api = avatar_api
                    with BrainBox.Api.serverless_test([Mock()]) as api:
                        Chara.Apis.brainbox_api = api
                        result = Chara.call(pipe)()

        self.assertEqual(4, len(result))
        self.assertIsInstance(result[0].template, Template)
        names = {r.original_template_name for r in result}
        self.assertIn(Template("yes").get_name(), names)
        self.assertIn(Template("no").get_name(), names)
