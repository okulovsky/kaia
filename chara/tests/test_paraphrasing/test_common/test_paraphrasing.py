from chara.paraphrasing.common import Paraphrase
from chara.common import Chara, CaseCollection
from chara.common.tools.llm import PromptTaskBuilder
from unittest import TestCase
from brainbox import BrainBox, ISelfManagingDecider
from foundation_kaia.misc import Loc
from grammatron import Template, OptionsDub
import json


class Mock(ISelfManagingDecider):
    def get_name(self):
        return "Ollama"

    def question(self, prompt: str, system_prompt: str | None = None, options: dict | None = None, num_predict: int | None = None):
        if prompt == 'TEST':
            return "* {item} не в списке покупок\n* {item} не найден"
        if "You now need to translate" in prompt:
            if 'banana' in prompt:
                return 'банан'
            elif 'orange' in prompt:
                return 'апельсин'
            else:
                raise ValueError(prompt)
        if "Ты - учитель русского языка" in prompt:
            if "du" in prompt.lower() or "you" in prompt.lower():
                raise ValueError("Mixing languages in grammar prompt!")
            return json.dumps({
                "text": "...",
                "grammar": {
                    "{item}": {
                        "падеж": "Именительный"
                    }
                }
            })
        if 'You are working on creating a comprehensive dataset' in prompt:
            return "* киви\n* манго\n"
        raise ValueError(prompt)


class ParaphraseTestCase(TestCase):
    def test_paraphrase(self):
        builder = PromptTaskBuilder('test')
        builder.read_prompt('TEST')
        settings = Paraphrase.Settings(
            paraphrase_task_builder=builder,
            enable_words_translation=True,
            grammar_correction_attempts=2,
            words_translation_attempts=2,
            enable_options_expanding=True,
        )
        options = OptionsDub(['banana', 'orange']).as_variable("item")
        cases = CaseCollection([Paraphrase.Case(
            Template(f"{options} is not in the shopping list"),
            'ru'
        )])

        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            pipe = Paraphrase.Pipeline(settings)
            with BrainBox.Api.serverless_test([Mock()]) as api:
                Chara.Apis.brainbox_api = api
                result = Chara.call(pipe)(cases).cases

        self.assertEqual(2, len(result))
        s = result[0].resulting_template.utter('киви').to_str()
        self.assertEqual('киви не в списке покупок', s)

        for value in ['киви', 'манго']:
            for case in result:
                case.resulting_template.utter(value).to_str()
