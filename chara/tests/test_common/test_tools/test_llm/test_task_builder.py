import tempfile
from pathlib import Path
from unittest import TestCase
from chara.common.tools.llm.prompt_task_builder import PromptTaskBuilder
from dataclasses import dataclass
from foundation_kaia.misc import Loc

@dataclass
class Obj:
    text: str
    language: str


class IntegrationTaskBuilder(TestCase):
    def _get_builder(self, file_content: str):
        builder = PromptTaskBuilder(model='model', case_to_key=lambda c: c.language)
        builder.read_prompt(file_content)
        return builder

    def test_language_keyed_prompts_content(self):
        builder = self._get_builder("Translate: {{ text }}\n# KEY ru\nПереведи: {{ text }}\n")
        self.assertEqual("Переведи: hello", builder._get_prompt(Obj(text='hello', language='ru')))
        self.assertEqual("Translate: hello", builder._get_prompt(Obj(text='hello', language='en')))
        self.assertEqual("Translate: hello", builder._get_prompt(Obj(text='hello', language='de')))

    def test_known_key_used_over_default(self):
        builder = self._get_builder("Default: {{ text }}\n# KEY en\nEnglish: {{ text }}\n# KEY ru\nРусский: {{ text }}\n")
        self.assertEqual("English: hello", builder._get_prompt(Obj(text='hello', language='en')))
        self.assertEqual("Русский: hello", builder._get_prompt(Obj(text='hello', language='ru')))

    def test_unknown_key_falls_back_to_default(self):
        builder = self._get_builder("Default: {{ text }}\n# KEY ru\nРусский: {{ text }}\n")
        self.assertEqual("Default: hello", builder._get_prompt(Obj(text='hello', language='de')))

    def test_case_to_key_returns_none_uses_default(self):
        builder = PromptTaskBuilder(model='model', case_to_key=lambda c: None)
        builder.read_prompt("Default: {{ text }}\n# KEY ru\nРусский: {{ text }}\n")
        self.assertEqual("Default: hello", builder._get_prompt(Obj(text='hello', language='ru')))

    def test_no_case_to_key_single_default_prompt(self):
        builder = PromptTaskBuilder(model='model')
        builder.read_prompt("Hello: {{ text }}\n")
        self.assertEqual("Hello: world", builder._get_prompt(Obj(text='world', language='en')))

    def test_no_case_to_key_multiple_prompts_raises(self):
        builder = PromptTaskBuilder(model='model')
        builder.read_prompt("Default: {{ text }}\n# KEY ru\nРусский: {{ text }}\n")
        with self.assertRaises(ValueError):
            builder._get_prompt(Obj(text='hello', language='en'))

    def test_no_case_to_key_only_keyed_prompt_raises(self):
        builder = PromptTaskBuilder(model='model')
        builder.read_prompt("# KEY ru\nРусский: {{ text }}\n")
        with self.assertRaises(ValueError):
            builder._get_prompt(Obj(text='hello', language='ru'))

    def test_not_initialized_raises(self):
        builder = PromptTaskBuilder(model='model')
        with self.assertRaises(ValueError):
            builder._get_prompt(Obj(text='hello', language='en'))

    def test_unknown_key_without_default_raises(self):
        builder = self._get_builder("# KEY en\nEnglish: {{ text }}\n# KEY ru\nРусский: {{ text }}\n")
        with self.assertRaises(ValueError):
            builder._get_prompt(Obj(text='hello', language='de'))

    def test_prompter_constructor_arg(self):
        builder = PromptTaskBuilder(model='model', prompter=lambda c: f"prompt: {c.text}")
        self.assertEqual("prompt: hello", builder._get_prompt(Obj(text='hello', language='en')))

    def test_prompter_and_prompt_file_raises(self):
        with Loc.create_test_file() as file:
            file.write_text("some content")
            with self.assertRaises(ValueError):
                PromptTaskBuilder(model='model', prompter=lambda c: '', prompt_file=file)
