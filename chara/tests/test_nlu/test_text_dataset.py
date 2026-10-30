import json
import random
from pathlib import Path
from enum import Enum
from types import SimpleNamespace
from unittest import TestCase
from grammatron import Template, OptionsDub
from foundation_kaia.misc import Loc
from chara.common import Chara, CaseCollection, CasePrioritization
from chara.common.pipelines.case_prioritization import PrioritizationItem
from chara.paraphrasing.common import Paraphrase
from chara.nlu.datasets.text_dataset import TextDatasetPipeline, TextDatasetCase, TextDatasetFingerprint, TextDatasetPrioritization
from chara.nlu.scripts import create_dataset


class Day(Enum):
    Today = 0
    Tomorrow = 1


class TextDatasetExportTestCase(TestCase):
    def test_options_are_the_values_of_the_original_template(self):
        original = Template(f"Call {OptionsDub(['Yuki', 'Sakura']).as_variable('person')}").with_name('Intents.call')
        # As after the paraphrasing into Russian: the options are said in Russian
        dub = OptionsDub(['Yuki', 'Sakura'])
        dub.value_to_strs['Yuki'] = ['Юки']
        dub.value_to_strs['Sakura'] = ['Сакуре']
        translated = Template(ru=f"Позвони {dub.as_variable('person')}")
        case = SimpleNamespace(original_template=original, resulting_template=translated, target_language_code='ru')

        random.seed(0)
        records = TextDatasetPipeline.export([case], 30)

        text_to_value = {r['text']: r['values'][0]['value'] for r in records}
        self.assertEqual({'Позвони Юки': 'Yuki', 'Позвони Сакуре': 'Sakura'}, text_to_value)
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


class TextDatasetFingerprintTestCase(TestCase):
    def test_fingerprint(self):
        template = Template(
            f"Call {OptionsDub(['Yuki', 'Sakura']).as_variable('person')}",
            "Call somebody",
        ).with_name('Intents.call')
        cases = Paraphrase([TextDatasetCase(template, 'de', 'neutral')]).prepare()
        self.assertEqual(
            {
                TextDatasetFingerprint('Intents.call', 'person', 'de', 'neutral'),
                TextDatasetFingerprint('Intents.call', '', 'de', 'neutral'),
            },
            {case.to_fingerprint() for case in cases.cases}
        )


def _prepared_cases(templates, languages, moods) -> list[TextDatasetCase]:
    return list(Paraphrase([
        TextDatasetCase(template, language, mood)
        for mood in moods
        for language in languages
        for template in templates
    ]).prepare().cases)


def _write_finished_run(run: Path, cases: list[TextDatasetCase]):
    for case in cases:
        case.resulting_template = case.original_template

    def paraphrase():
        return cases

    Chara.start(run)
    Chara.call(paraphrase)()


CALL = Template("Call Yuki").with_name('Intents.call')
STOP = Template("Stop").with_name('Intents.stop')


class TextDatasetPrioritizationTestCase(TestCase):
    def collect(self, positives_folder: Path, cases: list[TextDatasetCase]) -> dict:
        items = {case.to_fingerprint(): PrioritizationItem(case.to_fingerprint(), [case]) for case in cases}
        TextDatasetPrioritization(positives_folder, CasePrioritization.Strategy.only_new, 100).collect_statistics(items)
        return {fingerprint.language: item.existing for fingerprint, item in items.items()}

    def test_existing_counts_finished_runs_only(self):
        with Loc.create_test_folder() as folder:
            _write_finished_run(folder/'$1', _prepared_cases([CALL], ['en'], ['neutral']))
            _write_finished_run(folder/'$2', _prepared_cases([CALL], ['en'], ['neutral']))
            (folder/'$3').mkdir()
            self.assertEqual({'en': 2, 'de': 0}, self.collect(folder, _prepared_cases([CALL], ['en', 'de'], ['neutral'])))

    def test_missing_folder(self):
        with Loc.create_test_folder() as folder:
            self.assertEqual({'en': 0}, self.collect(folder/'positives', _prepared_cases([CALL], ['en'], ['neutral'])))

    def test_only_new_selects_new_language_and_template(self):
        with Loc.create_test_folder() as folder:
            _write_finished_run(folder/'positives'/'$1', _prepared_cases([CALL], ['en'], ['neutral']))
            prioritization = TextDatasetPrioritization(folder/'positives', CasePrioritization.Strategy.only_new, 100)
            Chara.start(folder/'run')
            selected = prioritization(CaseCollection(_prepared_cases([CALL, STOP], ['en', 'de'], ['neutral'])))
            self.assertEqual(
                {('Intents.call', 'de'), ('Intents.stop', 'en'), ('Intents.stop', 'de')},
                {(case.to_fingerprint().template_name, case.to_fingerprint().language) for case in selected.successes}
            )

    def test_create_dataset_without_new_cases_does_not_paraphrase(self):
        with Loc.create_test_folder() as folder:
            _write_finished_run(folder/'positives'/'$1', _prepared_cases([CALL], ['en'], ['neutral']))
            # No BrainBox here: the pipeline would fail if it got to the paraphrasing
            path = create_dataset([CALL], folder=folder, languages=('en',), moods=('neutral',))
            records = json.loads(path.read_text())
            self.assertEqual([dict(text='Call Yuki', intent='Intents.call', values=[], language='en')], records)
            self.assertEqual(2, len([run for run in (folder/'positives').iterdir() if run.is_dir()]))
