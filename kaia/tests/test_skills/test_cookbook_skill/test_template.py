from kaia.skills.cookbook_skill import Recipe
from unittest import TestCase
from grammatron import DubParameters

class IngredientTempalteTestCase(TestCase):
    def test_all_fields(self):
        i = Recipe.Ingredient("salt", 10, 2, 'spoon')
        s = Recipe.Ingredient.template().to_str(i, DubParameters(spoken=False, language='en'))
        self.assertEqual(
            '2 spoons of salt (10 grams)',
            s
        )

    def test_name_alone(self):
        i = Recipe.Ingredient("salt")
        s = Recipe.Ingredient.template().to_str(i, DubParameters(spoken=False, language='en'))
        self.assertEqual("salt", s)

    def test_unit_without_amount(self):
        i = Recipe.Ingredient("salt", None, None, "spoon")
        s = Recipe.Ingredient.template().to_str(i, DubParameters(spoken=False, language='en'))
        self.assertEqual("A spoon of salt", s)

    def test_amount_and_unit_no_grams_plural(self):
        i = Recipe.Ingredient("salt", None, 3, "spoon")
        s = Recipe.Ingredient.template().to_str(i, DubParameters(spoken=False, language='en'))
        self.assertEqual("3 spoons of salt", s)

    def test_name_with_grams_only(self):
        i = Recipe.Ingredient("salt", 10, None, None)
        s = Recipe.Ingredient.template().to_str(i, DubParameters(spoken=False, language='en'))
        self.assertEqual("salt (10 grams)", s)

    def test_singular_amount_and_grams(self):
        i = Recipe.Ingredient("salt", 1, None, "spoon")
        s = Recipe.Ingredient.template().to_str(i, DubParameters(spoken=False, language='en'))
        self.assertEqual("A spoon of salt (1 gram)", s)