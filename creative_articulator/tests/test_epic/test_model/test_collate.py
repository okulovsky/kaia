import unittest

from creative_articulator.epic.model.algorithms import collate, similarity

from .support import fragment


class TestCollate(unittest.TestCase):
    def test_identical_fragments_are_matched_on_both_sides(self):
        incoming = (fragment('Hello world', 'new'),)
        base = (fragment('Hello world', 'old'),)
        collate(incoming, base)
        self.assertIs(base[0], incoming[0].match.matched_with)
        self.assertIs(incoming[0], base[0].match.matched_with)
        self.assertEqual(1.0, incoming[0].match.match)

    def test_small_edit_is_matched(self):
        incoming = (fragment('The quick brown fox leaps over the lazy dog'),)
        base = (fragment('The quick brown fox jumps over the lazy dog'),)
        collate(incoming, base)
        self.assertIsNotNone(incoming[0].match)
        self.assertGreater(incoming[0].match.match, 0.8)

    def test_unrelated_text_is_not_matched(self):
        incoming = (fragment('The quick brown fox jumps over the lazy dog'),)
        base = (fragment('Completely unrelated sentence about something else'),)
        collate(incoming, base)
        self.assertIsNone(incoming[0].match)
        self.assertIsNone(base[0].match)

    def test_empty_base_leaves_everything_unmatched(self):
        incoming = (fragment('A'), fragment('B'))
        collate(incoming, ())
        self.assertEqual([None, None], [f.match for f in incoming])

    def test_best_match_wins(self):
        incoming = (fragment('The quick brown fox jumps over the lazy dog'),)
        base = (
            fragment('The quick brown fox jumps over the lazy cat', 'close'),
            fragment('The quick brown fox jumps over the lazy dog', 'exact'),
        )
        collate(incoming, base)
        self.assertEqual('exact', incoming[0].match.matched_with.payload)

    def test_matching_is_one_to_one(self):
        incoming = (fragment('Hello world', 'first'), fragment('Hello world', 'second'))
        base = (fragment('Hello world', 'old'),)
        collate(incoming, base)
        matched = [f for f in incoming if f.match is not None]
        self.assertEqual(1, len(matched))

    def test_reordering_is_followed(self):
        incoming = (fragment('Second fragment of the text', 1), fragment('First fragment of the text', 2))
        base = (fragment('First fragment of the text', 'a'), fragment('Second fragment of the text', 'b'))
        collate(incoming, base)
        self.assertEqual('b', incoming[0].match.matched_with.payload)
        self.assertEqual('a', incoming[1].match.matched_with.payload)

    def test_stale_matches_are_cleared(self):
        incoming = (fragment('Some fairly long text to compare with'),)
        base = (fragment('Some fairly long text to compare with'),)
        collate(incoming, base)
        collate(incoming, base + (fragment('Something entirely different here now'),))
        self.assertIsNotNone(incoming[0].match)
        collate(incoming, (fragment('Something entirely different here now'),))
        self.assertIsNone(incoming[0].match)

    def test_threshold_is_respected(self):
        incoming = (fragment('The quick brown fox jumps over the lazy dog'),)
        base = (fragment('The quick brown fox jumps over the lazy cat'),)
        collate(incoming, base, 0.99)
        self.assertIsNone(incoming[0].match)
        collate(incoming, base, 0.5)
        self.assertIsNotNone(incoming[0].match)


class TestSimilarity(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(1.0, similarity(fragment('abc'), fragment('abc')))

    def test_empty(self):
        self.assertEqual(1.0, similarity(fragment(''), fragment('')))

    def test_is_symmetric(self):
        a, b = fragment('The house at the edge'), fragment('The house near the edge')
        self.assertEqual(similarity(a, b), similarity(b, a))

    def test_long_texts_fall_back_to_simhash(self):
        text = 'a rather long sentence about nothing in particular. ' * 200
        a, b = fragment(text), fragment(text)
        self.assertGreater(len(text), 5000)
        self.assertEqual(1.0, similarity(a, b))


if __name__ == '__main__':
    unittest.main()
