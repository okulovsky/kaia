import unittest
from grammatron.grammars.ru import Declinator

class TestFindStandardFormWords(unittest.TestCase):
    def test_nouns_in_standard_form(self):
        words = ['стол', 'мамы', 'окно', 'окна']
        # Only masculine singular nominative nouns should be selected
        expected_indices = [0, 2]  # 'стол', 'дом'
        self.assertEqual(expected_indices, Declinator.choose_words_in_vocabular_form(words), )

    def test_adjectives_in_standard_form(self):
        words = ['красивая', 'красной', 'красивому', 'красивые']
        expected_indices = [0]  # only masculine singular nominative
        self.assertEqual(expected_indices, Declinator.choose_words_in_vocabular_form(words))

    def test_cardinal_numerals(self):
        words = ['три', "трех", 'один', 'четырехсот']
        expected_indices = [0, 2]
        self.assertEqual(expected_indices, Declinator.choose_words_in_vocabular_form(words))

    def test_ordinal_numerals(self):
        words = ['первый', 'первая', 'первое', 'вторым', 'третьим']
        expected_indices = [0, 1, 2]  # 'первый', 'третий'
        self.assertEqual(expected_indices, Declinator.choose_words_in_vocabular_form(words))


    def test_empty_and_non_matching(self):
        words = ['и', 'на', 'в', 'собака', 'море', 'красная']
        # None of these are valid: either particles or wrong gender
        expected_indices = [3,4,5]
        self.assertEqual(Declinator.choose_words_in_vocabular_form(words), expected_indices)
