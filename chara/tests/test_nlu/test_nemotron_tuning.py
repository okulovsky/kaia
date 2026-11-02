import random
import sys
from pathlib import Path
from unittest import TestCase
import chara

sys.path.insert(0, str(Path(chara.__file__).parent/'nlu'/'nemotron_tuning'))
import manifest  # noqa: E402
import metrics  # noqa: E402
import words  # noqa: E402


class MadeUpWordsTestCase(TestCase):
    def test_same_seed_same_words(self):
        first = words.made_up_words('ru', words.NAME, 20, random.Random(1), set())
        second = words.made_up_words('ru', words.NAME, 20, random.Random(1), set())
        self.assertEqual(first, second)

    def test_known_words_are_not_generated(self):
        known = set()
        taken = words.made_up_words('de', words.THING, 200, random.Random(1), known)
        again = words.made_up_words('de', words.THING, 200, random.Random(1), known)
        self.assertEqual(200, len(set(taken)))
        self.assertEqual(set(), {w.lower() for w in taken} & {w.lower() for w in again})

    def test_case(self):
        rnd = random.Random(1)
        self.assertTrue(words.made_up_word('en', words.NAME, rnd)[0].isupper())
        self.assertTrue(words.made_up_word('en', words.THING, rnd)[0].islower())
        self.assertTrue(words.made_up_word('de', words.THING, rnd)[0].isupper())
        self.assertTrue(words.made_up_word('ru', words.PLACE, rnd)[0].islower())

    def test_names_go_only_to_the_skills_with_names(self):
        for language in words.LANGUAGES:
            result = words.phrases(language, 'names', 40, random.Random(1), set())
            self.assertEqual({'call', 'meeting'}, {p['skill'] for p in result})
            self.assertEqual(set(words.NAMES[language]), {p['word'] for p in result})

    def test_every_group_and_skill_makes_a_phrase_with_the_word(self):
        for language in words.LANGUAGES:
            for group in words.GROUPS:
                for phrase in words.phrases(language, group, 8, random.Random(1), set()):
                    self.assertIn(phrase['word'], phrase['text'])
                    self.assertNotIn('{', phrase['text'])

    def test_unseen_carriers_are_not_in_the_training_carriers(self):
        for language in words.LANGUAGES:
            seen = {c for skill in words.SKILLS[language].values() for c in skill.carriers}
            unseen = {c for skill in words.UNSEEN_SKILLS[language].values() for c in skill.carriers}
            self.assertEqual(set(), seen & unseen)

    def test_every_group_makes_an_unseen_phrase_with_the_word(self):
        for language in words.LANGUAGES:
            for group in words.GROUPS:
                for phrase in words.phrases(language, group, 8, random.Random(1), set(), words.UNSEEN_SKILLS):
                    self.assertIn(phrase['word'], phrase['text'])
                    self.assertNotIn('{', phrase['text'])

    def test_test_and_train_words_do_not_overlap(self):
        rnd, known = random.Random(1), set()
        test = words.phrases('ru', 'new', 100, rnd, known)
        train = words.phrases('ru', 'new', 100, rnd, known)
        self.assertEqual(set(), {p['word'] for p in test} & {p['word'] for p in train})


class SlotResultTestCase(TestCase):
    def test_all_is_right(self):
        result = metrics.slot_result('Позвони Бахуру, пожалуйста.', 'Бахуру', 'позвони бахуру пожалуйста')
        self.assertTrue(result['slot_exact'])
        self.assertEqual(0, result['neighbour_errors'])
        self.assertEqual(2, result['neighbour_words'])

    def test_close_spelling_is_not_a_neighbour_error(self):
        result = metrics.slot_result('Добавь мумзики в список покупок.', 'мумзики', 'Добавь мамзики в список покупок.')
        self.assertFalse(result['slot_exact'])
        self.assertTrue(result['slot_close'])
        self.assertEqual(0, result['neighbour_errors'])
        self.assertEqual('мамзики', result['heard'])

    def test_word_split_in_two_is_still_the_slot(self):
        result = metrics.slot_result('Call Kirishima.', 'Kirishima', 'call kiri shima')
        self.assertTrue(result['slot_exact'])
        self.assertEqual(0, result['neighbour_errors'])

    def test_broken_neighbours_are_counted(self):
        result = metrics.slot_result('Ruf Todoroki sofort an.', 'Todoroki', 'roof the rocky so fort on')
        self.assertFalse(result['slot_close'])
        self.assertEqual(3, result['neighbour_errors'])

    def test_empty_hypothesis(self):
        result = metrics.slot_result('Call Kirishima.', 'Kirishima', '')
        self.assertEqual(1.0, result['slot_errors'])
        self.assertEqual(1, result['neighbour_errors'])

    def test_word_of_two_words(self):
        result = metrics.slot_result('Turn on the light in the living room.', 'living room', 'turn on the light in the living room')
        self.assertTrue(result['slot_exact'])
        self.assertEqual(0, result['neighbour_errors'])

    def test_summary(self):
        rows = [
            dict(text='Call Anna.', word='Anna', hypothesis='call anna'),
            dict(text='Call Kirishima.', word='Kirishima', hypothesis=''),
        ]
        summary = metrics.summary(rows)
        self.assertEqual(2, summary['count'])
        self.assertEqual(0.5, summary['slot_exact'])
        self.assertEqual(0.5, summary['neighbour_wer'])
        self.assertEqual(0.5, summary['empty'])


class ManifestTestCase(TestCase):
    def test_yo_is_the_same_as_ye(self):
        self.assertEqual(manifest.normalize('Ещё раз!'), manifest.normalize('еще раз'))

    def test_transcript_closes_with_the_language_tag(self):
        self.assertEqual('Call Anna. <en-US>', manifest.transcript(dict(text='Call Anna.', language='en-US')))
