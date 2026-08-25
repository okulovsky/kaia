import unittest

from creative_articulator.epic.model import ParagraphArray
from creative_articulator.epic.model.algorithms import separate, separate_to_known_base

from .support import joined, texts

TEXT = (
    'The house stood at the edge of the forest.\n'
    'Nobody had lived there for many years.\n'
    '\n'
    '- Do you hear that? asked Anna.\n'
    '- I hear nothing at all, said Peter.\n'
    '\n'
    'The wind moved through the empty windows.\n'
)

MAX_LENGTH = 120


def base_of(text: str):
    return separate(ParagraphArray.parse(text), MAX_LENGTH)


def separated(text: str, base):
    return separate_to_known_base(ParagraphArray.parse(text), base, MAX_LENGTH)


class TestSeparateToKnownBase(unittest.TestCase):
    def test_empty_text_gives_no_blocks(self):
        self.assertEqual([], separate_to_known_base(ParagraphArray(), base_of(TEXT), MAX_LENGTH))

    def test_without_a_base_it_still_separates(self):
        result = separated(TEXT, [])
        self.assertGreater(len(result), 1)
        self.assertEqual(TEXT, joined(result))

    def test_blocks_are_a_lossless_partition(self):
        result = separated(TEXT + 'One more line at the end.\n', base_of(TEXT))
        self.assertEqual(TEXT + 'One more line at the end.\n', joined(result))

    def test_max_length_is_respected(self):
        for block in separated(TEXT + 'One more line at the end.\n', base_of(TEXT)):
            self.assertLessEqual(block.paragraphs.length, MAX_LENGTH)

    def test_unchanged_text_keeps_the_old_separation(self):
        base = base_of(TEXT)
        result = separated(TEXT, base)
        self.assertEqual(texts(base), texts(result))

    def test_unchanged_text_matches_every_old_block(self):
        base = base_of(TEXT)
        result = separated(TEXT, base)
        self.assertEqual([b.paragraphs.text for b in base], [f.match.matched_with.paragraphs.text for f in result])

    def test_untouched_blocks_survive_an_insertion(self):
        base = base_of(TEXT)
        edited = TEXT + '\nA brand new paragraph appears here.\nAnd a second new line follows it.\n'
        result = separated(edited, base)
        preserved = set(texts(result)) & set(texts(base))
        self.assertEqual(set(texts(base)), preserved)

    def test_new_text_is_not_matched(self):
        base = base_of(TEXT)
        edited = TEXT + '\nA brand new paragraph appears here.\nAnd a second new line follows it.\n'
        result = separated(edited, base)
        unmatched = [f for f in result if f.match is None]
        self.assertEqual(1, len(unmatched))
        self.assertIn('A brand new paragraph', unmatched[0].paragraphs.text)

    def test_matching_is_one_to_one(self):
        base = base_of(TEXT)
        result = separated(TEXT + TEXT, base)
        matched = [f.match.matched_with for f in result if f.match is not None]
        self.assertEqual(len(matched), len(set(id(m) for m in matched)))


if __name__ == '__main__':
    unittest.main()
