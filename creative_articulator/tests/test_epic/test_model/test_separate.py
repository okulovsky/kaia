import unittest

from creative_articulator.epic.model import ParagraphArray
from creative_articulator.epic.model.algorithms import separate

from .support import joined, paragraphs, texts

TEXT = (
    'The house stood at the edge of the forest.\n'
    'Nobody had lived there for many years.\n'
    '\n'
    '- Do you hear that? asked Anna.\n'
    '- I hear nothing at all, said Peter.\n'
    '- Then you are not listening, she said.\n'
    '\n'
    'The wind moved through the empty windows.\n'
)


def blocks(text: str, max_length: int):
    return separate(ParagraphArray.parse(text), max_length)


class TestSeparate(unittest.TestCase):
    def test_empty_text_gives_no_blocks(self):
        self.assertEqual([], separate(ParagraphArray(), 100))

    def test_short_text_is_one_block(self):
        self.assertEqual(1, len(blocks(TEXT, 10000)))

    def test_blocks_are_a_lossless_partition(self):
        for max_length in (40, 80, 120, 300):
            self.assertEqual(TEXT, joined(blocks(TEXT, max_length)))

    def test_no_block_is_empty(self):
        for block in blocks(TEXT, 60):
            self.assertGreater(len(block.paragraphs), 0)

    def test_max_length_is_respected(self):
        for block in blocks(TEXT, 120):
            self.assertLessEqual(block.paragraphs.length, 120)

    def test_single_oversized_paragraph_becomes_its_own_block(self):
        text = 'short line\n' + 'x' * 500 + '\nanother short line'
        result = blocks(text, 100)
        oversized = [b for b in result if b.paragraphs.length > 100]
        self.assertEqual(1, len(oversized))
        self.assertEqual(1, len(oversized[0].paragraphs))

    def test_payload_and_match_are_left_to_the_caller(self):
        for block in blocks(TEXT, 60):
            self.assertIsNone(block.payload)
            self.assertIsNone(block.match)


class TestSeparationQuality(unittest.TestCase):
    def test_dialog_lines_are_kept_together(self):
        result = blocks(TEXT, 150)
        dialogs = [text for text in texts(result) if 'asked Anna' in text]
        self.assertEqual(1, len(dialogs))
        self.assertIn('I hear nothing at all', dialogs[0])
        self.assertIn('you are not listening', dialogs[0])

    def test_cuts_are_preferred_at_blank_lines(self):
        result = blocks(TEXT, 150)
        for block in result[:-1]:
            self.assertEqual(paragraphs('')[0].text_type, block.paragraphs[-1].text_type)

    def test_blocks_tend_to_be_big(self):
        result = blocks(TEXT, 10000)
        self.assertEqual(1, len(result))
        result = blocks(TEXT, 150)
        self.assertLessEqual(len(result), 3)


if __name__ == '__main__':
    unittest.main()
