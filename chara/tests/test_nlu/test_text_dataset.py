import random
from enum import Enum
from types import SimpleNamespace
from unittest import TestCase
from grammatron import Template, OptionsDub
from chara.nlu.datasets.text_dataset import TextDatasetPipeline


class Day(Enum):
    Today = 0
    Tomorrow = 1


class TextDatasetExportTestCase(TestCase):
    def test_options_are_the_values_of_the_original_template(self):
        original = Template(f"Call {OptionsDub(['Yuki', 'Sakura']).as_variable('person')}").with_name('Intents.call')
        # As after the paraphrasing into Russian: the options are said in Russian, and OptionExpanding added one more
        dub = OptionsDub(['Yuki', 'Sakura'])
        dub.value_to_strs['Yuki'] = ['Юки']
        dub.value_to_strs['Sakura'] = ['Сакуре']
        dub.value_to_strs['Маме'] = ['Маме']
        translated = Template(ru=f"Позвони {dub.as_variable('person')}")
        case = SimpleNamespace(original_template=original, resulting_template=translated, target_language_code='ru')

        random.seed(0)
        records = TextDatasetPipeline.export([case], 30)

        text_to_value = {r['text']: r['values'][0]['value'] for r in records}
        self.assertEqual({'Позвони Юки': 'Yuki', 'Позвони Сакуре': 'Sakura', 'Позвони Маме': 'Маме'}, text_to_value)
        self.assertEqual({'Intents.call'}, {r['intent'] for r in records})
        self.assertEqual({'ru'}, {r['language'] for r in records})

    def test_enum_options(self):
        original = Template(f"What date is {OptionsDub(Day).as_variable('delta')}?").with_name('Intents.date')
        dub = OptionsDub(Day)
        dub.value_to_strs[Day.Today] = ['сегодня']
        dub.value_to_strs[Day.Tomorrow] = ['завтра']
        translated = Template(ru=f"Какое число {dub.as_variable('delta')}?")
        case = SimpleNamespace(original_template=original, resulting_template=translated, target_language_code='ru')

        random.seed(0)
        records = TextDatasetPipeline.export([case], 20)

        text_to_value = {r['text']: r['values'][0]['value'] for r in records}
        english = OptionsDub(Day)
        self.assertEqual({'Какое число сегодня?': english.to_str(Day.Today), 'Какое число завтра?': english.to_str(Day.Tomorrow)},
                         text_to_value)
