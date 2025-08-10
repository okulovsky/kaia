from unittest import TestCase
from grammatron.grammars.ru import *

import unittest

class TestDeclinator(unittest.TestCase):
    def test_declinate_all_vocab_form_words(self):
        text = "десять"
        result = Declinator.declinate(
            text,
            declension=RuDeclension.DATIVE,
        )
        self.assertEqual("десяти", result)

    def test_declinate_only_selected_words(self):
        text = "синяя кружка и ложка"
        result = Declinator.declinate(
            text,
            declension=RuDeclension.INSTRUMENTAL,
            gender=RuGender.FEMININE,
            number=RuNumber.SINGULAR,
            word_selector=lambda words: [0, 1]  # синяя, кружка
        )
        self.assertEqual("синей кружкой и ложка", result)

    def test_mixed_selection_with_punctuation(self):
        text = "вкусный кофе, свежий круассан"
        result = Declinator.declinate(
            text,
            declension=RuDeclension.GENITIVE,
            gender=RuGender.MASCULINE,
            number=RuNumber.SINGULAR,
            word_selector=lambda words: [0, 2, 3]  # вкусный, свежий, круассан
        )
        self.assertEqual("вкусного кофе, свежего круассана", result)

    def test_no_selector_no_change(self):
        text = "дом"
        result = Declinator.declinate(text)
        self.assertEqual(result, "дом")

    def test_empty_text(self):
        result = Declinator.declinate("")
        self.assertEqual("", result)

    def test_declinate_phrase_with_conjunctions(self):
        text = "первый и второй этаж"
        result = Declinator.declinate(
            text,
            declension=RuDeclension.PREPOSITIONAL,
            gender=RuGender.MASCULINE,
            number=RuNumber.SINGULAR
        )
        self.assertEqual("первом и втором этаже", result)

    def test_partial_declension_feminine(self):
        text = "первая миска супа"
        result = Declinator.declinate(
            text,
            declension=RuDeclension.INSTRUMENTAL,
            gender=RuGender.FEMININE,
            number=RuNumber.SINGULAR,
            word_selector=lambda words: [0, 1]  # первая, миска
        )
        self.assertEqual("первой миской супа", result)

    def test_cardinal_declension(self):
        text = 'десять'
        result = Declinator.declinate(
            text,
            declension=RuDeclension.INSTRUMENTAL
        )
        self.assertEqual("десятью", result)

    def test_cardinal_gender_declension(self):
        text = 'два'
        result = Declinator.declinate(
            text,
            gender=RuGender.FEMININE
        )
        self.assertEqual("две", result)