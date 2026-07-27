import unittest
from enum import Enum
from typing import Optional
from chara.common.tools.llm.question import Question


class Mood(Enum):
    HAPPY = 'happy'
    SAD = 'sad'


class QuestionPostInitTestCase(unittest.TestCase):

    # --- bool: closed, full domain auto-filled ---

    def test_bool_is_closed_with_full_domain(self):
        q = Question('flag', 'a flag', bool)
        self.assertTrue(q.is_closed)
        self.assertEqual([True, False], q.options)

    def test_optional_bool_is_closed_with_none_in_domain(self):
        q = Question('flag', 'a flag', Optional[bool])
        self.assertTrue(q.is_closed)
        self.assertEqual([True, False, None], q.options)

    # --- Enum: closed, full domain auto-filled ---

    def test_enum_is_closed_with_full_domain(self):
        q = Question('mood', 'a mood', Mood)
        self.assertTrue(q.is_closed)
        self.assertEqual([Mood.HAPPY, Mood.SAD], q.options)

    def test_optional_enum_is_closed_with_none_in_domain(self):
        q = Question('mood', 'a mood', Optional[Mood])
        self.assertTrue(q.is_closed)
        self.assertEqual([Mood.HAPPY, Mood.SAD, None], q.options)

    # --- int/float: open, default examples auto-filled when not given ---

    def test_int_without_options_gets_default_examples(self):
        q = Question('age', 'an age', int)
        self.assertFalse(q.is_closed)
        self.assertEqual([1, 2, 3], q.options)

    def test_float_without_options_gets_default_examples(self):
        q = Question('score', 'a score', float)
        self.assertFalse(q.is_closed)
        self.assertEqual([1.0, 1.5, 2.0], q.options)

    def test_int_with_explicit_options_keeps_them(self):
        q = Question('age', 'an age', int, options=[7, 8])
        self.assertFalse(q.is_closed)
        self.assertEqual([7, 8], q.options)

    # --- str: open, no default examples exist, so options are mandatory ---

    def test_str_without_options_raises(self):
        with self.assertRaises(ValueError):
            Question('name', 'a name', str)

    def test_str_with_explicit_options_keeps_them(self):
        q = Question('name', 'a name', str, options=['Sam', 'Al'])
        self.assertFalse(q.is_closed)
        self.assertEqual(['Sam', 'Al'], q.options)

    # --- explicit is_closed overrides the type-based default ---

    def test_explicit_is_closed_false_on_bool_is_respected(self):
        q = Question('flag', 'a flag', bool, is_closed=False)
        self.assertFalse(q.is_closed)
        # Domain auto-fill is driven by type, not by the is_closed override.
        self.assertEqual([True, False], q.options)

    def test_explicit_is_closed_true_on_int_is_respected(self):
        q = Question('age', 'an age', int, options=[7, 8], is_closed=True)
        self.assertTrue(q.is_closed)
        self.assertEqual([7, 8], q.options)


if __name__ == '__main__':
    unittest.main()
