from unittest import TestCase
from ..skill.recognize_food import FoodRecognizer

class FoodRecognizerTestCase(TestCase):
    def check(self, s, amount, unit, food):
        rec = FoodRecognizer()
        record = rec.parse(s)
        if amount is None:
            self.assertIsNone(record)
            return
        self.assertEqual(amount, record.amount)
        self.assertEqual(unit, record.unit)
        self.assertEqual(food, record.food)

    def test_simple(self):
        self.check('I ate two spoons of protein', 2, 'spoon', 'protein')

    def test_no_leading_words(self):
        self.check('Three cups of milk', 3, 'cup', 'milk')

    def test_no_count(self):
        self.check('A glass of wine', 1, 'glass', 'wine')

    def test_no_unit(self):
        self.check('I eat one carrot',1,'portion','carrot')


    def test_numeric_input(self):
        self.check('25.2 grams of tea', 25.2, 'gram', 'tea')

    def test_food_only(self):
        self.check('A carrot', 1, 'portion','carrot')

    def test_food_a(self):
        self.check('Apricot', 1, 'portion', 'apricot')

