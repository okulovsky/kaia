from chara.common import logger, CharaApis
from chara.common.tools.llm import PromptTaskBuilder
from chara.paraphrasing.basic_pipelines.template_words_translation import WordTranslationPipeline, WordTranslationCache
from unittest import TestCase
from chara.tests.test_voice_clone.test_common.test_chatterbox import ChatterboxTrainTest
from grammatron import Template, OptionsDub, CardinalDub, PluralAgreement
from foundation_kaia.misc import Loc
from brainbox import BrainBox, ISelfManagingDecider
from brainbox.deciders import Collector


class OllamaMock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt):
        word, language = prompt.split('/')
        if word == 'minute' and language == 'ru':
            return "минута"
        if word == 'banana' and language == 'ru':
            return "банан"
        if word == 'orange' and language == 'ru':
            return "апельсин"
        if word == 'bathroom' and language == 'de':
            return "Badezimmer"
        if word == 'living room' and language == 'de':
            return "Wohnzimmer"
        raise ValueError(f"Wrong request {prompt}")


def f(case):
    return case.source+'/'+case.target_language_code

class TestWordTranslationPipeline(TestCase):
    def test_word_translation_pipeline(self):
        templates = [
            Template(ru=f"Таймер заведен на {PluralAgreement(CardinalDub().as_variable('amount'), 'minute')}"),
            Template(ru=f"Нужно купить {OptionsDub(['banana', 'orange']).as_variable('fruit')}"),
            Template(de=f"Ich gehe in {OptionsDub(['bathroom', 'living room']).as_variable('room')}")
        ]
        with Loc.create_test_folder() as folder:
            with BrainBox.Api.serverless_test([OllamaMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                cache = WordTranslationCache(folder)
                pipe = WordTranslationPipeline(PromptTaskBuilder("test", f))
                pipe(cache, templates)
                result = cache.read_result()

        self.assertEqual("Таймер заведен на десять минут", result[0].utter(10).to_str())
        self.assertEqual("Нужно купить банан", result[1].utter('banana').to_str())
        self.assertEqual("Ich gehe in Wohnzimmer", result[2].utter("living room").to_str())


    def test_with_translating_headers(self):
        templates = [
            Template(ru=f"Таймер заведен на {PluralAgreement(CardinalDub().as_variable('amount'), 'minute')}"),
            Template(ru=f"Нужно купить {OptionsDub(['banana', 'orange']).as_variable('fruit')}"),
            Template(de=f"Ich gehe in {OptionsDub(['bathroom', 'living room']).as_variable('room')}")
        ]
        with Loc.create_test_folder() as folder:
            with BrainBox.Api.serverless_test([OllamaMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                cache = WordTranslationCache(folder)
                pipe = WordTranslationPipeline(PromptTaskBuilder("test", f), also_translate_option_headers=True)
                pipe(cache, templates)
                result = cache.read_result()

        self.assertEqual("Таймер заведен на десять минут", result[0].utter(10).to_str())
        #self.assertEqual("Нужно купить банан", result[1].utter('банан').to_str())
        #self.assertEqual("Ich gehe in Wohnzimmer", result[2].utter("Wohnzimmer").to_str())


