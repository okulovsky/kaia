from avatar.app import AvatarApi
from unittest import TestCase
from grammatron import Template
from chara.paraphrasing.utterances import (
    NewEntitiesSelection, UtteranceParaphraseCaseManager, UtteranceParaphrasePipeline)
from chara.paraphrasing.utterances.reporting import REPORT_FILENAME
from chara.paraphrasing.common import Paraphrase
from chara.paraphrasing.utterances.prompter import create_default_utterance_request
from chara.common import Chara
from chara.common.llm import BrainBoxLLMEngine, LLMSetup
from foundation_kaia.misc import Loc
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Ollama
from foundation_kaia.marshalling import FileLike


class Mock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: Ollama.Options | None = None, image: FileLike | None = None) -> str:
        return "* Sure!\n* Yep!"


class UtterancePipelineTestCase(TestCase):
    def test_pipeline(self):
        setup = LLMSetup(BrainBoxLLMEngine(), 'test')
        settings = Paraphrase.Settings(
            paraphrase_request=create_default_utterance_request(setup),
            enable_words_translation=False,
            grammar_correction_attempts=None,
            enable_options_expanding=False,
        )
        manager = UtteranceParaphraseCaseManager(
            [Template("yes"), Template("no")],
            target_languages=('en',)
        )
        pipe = UtteranceParaphrasePipeline(manager, settings, NewEntitiesSelection(batch_size=10))

        with Loc.create_test_folder() as avatar_folder:
            with Loc.create_test_folder() as folder:
                Chara.start(folder)
                with AvatarApi.test(avatar_folder) as avatar_api:
                    Chara.Apis.avatar_api = avatar_api
                    with BrainBox.Api.serverless_test([Mock()]) as api:
                        Chara.Apis.brainbox_api = api
                        result = Chara.call(pipe)()
                reports = list(folder.rglob(REPORT_FILENAME))
                self.assertEqual(1, len(reports))
                report = reports[0].read_text(encoding='utf-8')

        self.assertEqual(4, len(result))
        self.assertIsInstance(result[0].template, Template)
        names = {r.original_template_name for r in result}
        self.assertIn(Template("yes").get_name(), names)
        self.assertIn(Template("no").get_name(), names)

        self.assertIn('4 new paraphrase(s)', report)
        for name in names:
            self.assertIn(name, report)
