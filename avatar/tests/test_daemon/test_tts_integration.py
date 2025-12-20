import unittest
from avatar.daemon.tts_integration_service import simple_sent_tokenize

class TestSimpleSentTokenize(unittest.TestCase):
    def test_basic_sentences(self):
        text = "Hello world! This is a test. It works? Well, mostly."
        expected = [
            "Hello world!",
            "This is a test.",
            "It works?",
            "Well, mostly."
        ]
        self.assertEqual(simple_sent_tokenize(text), expected)

    def test_with_multiple_spaces(self):
        text = "Hello world!   This is spaced weirdly."
        expected = [
            "Hello world!",
            "This is spaced weirdly."
        ]
        self.assertEqual(simple_sent_tokenize(text), expected)

    def test_with_newlines(self):
        text = "Hello world!\nThis is on a new line."
        expected = [
            "Hello world!",
            "This is on a new line."
        ]
        self.assertEqual(simple_sent_tokenize(text), expected)

    def test_trailing_spaces(self):
        text = "Hello world! This is a test.   "
        expected = [
            "Hello world!",
            "This is a test."
        ]
        self.assertEqual(simple_sent_tokenize(text), expected)

    def test_russian_text(self):
        text = "Привет, мир! Это тест. Всё работает?"
        expected = [
            "Привет, мир!",
            "Это тест.",
            "Всё работает?"
        ]
        self.assertEqual(simple_sent_tokenize(text), expected)
