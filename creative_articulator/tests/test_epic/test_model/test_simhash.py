import unittest

from creative_articulator.epic.model import hamming_distance, simhash


class TestSimhash(unittest.TestCase):
    def test_identical_text_produces_identical_hash(self):
        a = simhash('The quick brown fox jumps over the lazy dog')
        b = simhash('The quick brown fox jumps over the lazy dog')
        self.assertEqual(a, b)

    def test_empty_text_is_zero(self):
        self.assertEqual(0, simhash(''))
        self.assertEqual(0, simhash('   '))

    def test_similar_text_is_close_in_hamming_distance(self):
        a = simhash('The quick brown fox jumps over the lazy dog')
        b = simhash('The quick brown fox leaps over the lazy dog')
        self.assertLess(hamming_distance(a, b), 10)

    def test_unrelated_text_is_far_in_hamming_distance(self):
        a = simhash('The quick brown fox jumps over the lazy dog')
        b = simhash('Completely unrelated sentence about something else entirely')
        self.assertGreater(hamming_distance(a, b), 15)

    def test_similar_text_is_closer_than_unrelated_text(self):
        base = simhash('The quick brown fox jumps over the lazy dog')
        similar = simhash('The quick brown fox leaps over the lazy dog')
        unrelated = simhash('Completely unrelated sentence about something else entirely')
        self.assertLess(hamming_distance(base, similar), hamming_distance(base, unrelated))

    def test_word_order_does_not_matter(self):
        # simhash votes per-token, order-independent, unlike Levenshtein.
        a = simhash('alpha beta gamma')
        b = simhash('gamma beta alpha')
        self.assertEqual(a, b)

    def test_iterable_of_strings_matches_their_concatenation(self):
        joined = simhash('The quick brown fox jumps over the lazy dog')
        split = simhash(['The quick brown fox', 'jumps over the lazy dog'])
        self.assertEqual(joined, split)

    def test_empty_iterable_is_zero(self):
        self.assertEqual(0, simhash([]))
        self.assertEqual(0, simhash(['', '   ']))

    def test_iterable_is_order_independent(self):
        a = simhash(['alpha beta', 'gamma'])
        b = simhash(['gamma', 'alpha beta'])
        self.assertEqual(a, b)

    def test_generator_is_accepted(self):
        text = 'The quick brown fox jumps over the lazy dog'
        self.assertEqual(simhash(text), simhash(fragment for fragment in text.split(' ')))


class TestHammingDistance(unittest.TestCase):
    def test_zero_for_identical_hashes(self):
        self.assertEqual(0, hamming_distance(123456, 123456))

    def test_is_symmetric(self):
        a, b = 0b1010, 0b0110
        self.assertEqual(hamming_distance(a, b), hamming_distance(b, a))

    def test_counts_differing_bits(self):
        self.assertEqual(2, hamming_distance(0b0000, 0b0101))


if __name__ == '__main__':
    unittest.main()
