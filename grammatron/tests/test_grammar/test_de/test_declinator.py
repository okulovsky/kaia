import unittest
from grammatron.grammars.de import DeDeclinator, DeCasus, DeGenus, DeNumerus, DeArticleType


class TestDeDeclinator(unittest.TestCase):

    # ------------------------------------------------------------------
    # Nouns
    # ------------------------------------------------------------------

    def test_noun_genitiv_singular(self):
        # german_nouns returns 'Hunds' as primary genitiv singular; 'Hundes' is the alternative (marked with *)
        result = DeDeclinator.declinate('Hund', casus=DeCasus.GENITIV, numerus=DeNumerus.SINGULAR)
        self.assertEqual('Hunds', result)

    def test_noun_nominativ_plural(self):
        result = DeDeclinator.declinate('Haus', casus=DeCasus.NOMINATIV, numerus=DeNumerus.PLURAL)
        self.assertEqual('Häuser', result)

    def test_noun_dativ_plural(self):
        result = DeDeclinator.declinate('Hund', casus=DeCasus.DATIV, numerus=DeNumerus.PLURAL)
        self.assertEqual('Hunden', result)

    def test_noun_feminine_genitiv_singular(self):
        result = DeDeclinator.declinate('Frau', casus=DeCasus.GENITIV, numerus=DeNumerus.SINGULAR)
        self.assertEqual('Frau', result)

    def test_noun_neutrum_genitiv_singular(self):
        result = DeDeclinator.declinate('Kind', casus=DeCasus.GENITIV, numerus=DeNumerus.SINGULAR)
        self.assertEqual('Kindes', result)

    def test_unknown_noun_unchanged(self):
        result = DeDeclinator.declinate('Xyzblorp', casus=DeCasus.GENITIV, numerus=DeNumerus.SINGULAR)
        self.assertEqual('Xyzblorp', result)

    # ------------------------------------------------------------------
    # Adjective + noun phrases (no article — STRONG)
    # ------------------------------------------------------------------

    def test_adj_noun_strong_nominativ(self):
        result = DeDeclinator.declinate(
            'frischer Kaffee',
            casus=DeCasus.NOMINATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.STRONG,
        )
        self.assertEqual('frischer Kaffee', result)

    def test_adj_noun_strong_genitiv(self):
        result = DeDeclinator.declinate(
            'frischer Kaffee',
            casus=DeCasus.GENITIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.STRONG,
        )
        self.assertEqual('frischen Kaffees', result)

    def test_adj_noun_strong_dativ(self):
        result = DeDeclinator.declinate(
            'kleine Gurke',
            casus=DeCasus.DATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.STRONG,
        )
        self.assertEqual('kleiner Gurke', result)

    # ------------------------------------------------------------------
    # Adjective + noun phrases (with article — WEAK)
    # ------------------------------------------------------------------

    def test_adj_noun_weak_nominativ_masc(self):
        result = DeDeclinator.declinate(
            'kleine Hund',
            casus=DeCasus.NOMINATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.WEAK,
        )
        self.assertEqual('der kleine Hund', result)

    def test_adj_noun_weak_dativ_fem(self):
        result = DeDeclinator.declinate(
            'kleine Gurke',
            casus=DeCasus.DATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.WEAK,
        )
        self.assertEqual('der kleinen Gurke', result)

    def test_adj_noun_weak_akkusativ_masc(self):
        result = DeDeclinator.declinate(
            'große Hund',
            casus=DeCasus.AKKUSATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.WEAK,
        )
        self.assertEqual('den großen Hund', result)

    def test_adj_noun_weak_plural(self):
        result = DeDeclinator.declinate(
            'kleine Hund',
            casus=DeCasus.NOMINATIV, numerus=DeNumerus.PLURAL,
            article_type=DeArticleType.WEAK,
        )
        self.assertEqual('die kleinen Hunde', result)

    # ------------------------------------------------------------------
    # Adjective + noun phrases (indefinite article — MIXED)
    # ------------------------------------------------------------------

    def test_adj_noun_mixed_nominativ_masc(self):
        result = DeDeclinator.declinate(
            'kleine Hund',
            casus=DeCasus.NOMINATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.MIXED,
        )
        self.assertEqual('ein kleiner Hund', result)

    def test_adj_noun_mixed_dativ_fem(self):
        result = DeDeclinator.declinate(
            'kleine Gurke',
            casus=DeCasus.DATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.MIXED,
        )
        self.assertEqual('einer kleinen Gurke', result)

    def test_adj_noun_mixed_plural_no_article_strong_endings(self):
        # MIXED + PLURAL → no article, STRONG adjective endings
        result = DeDeclinator.declinate(
            'kleine Hund',
            casus=DeCasus.NOMINATIV, numerus=DeNumerus.PLURAL,
            article_type=DeArticleType.MIXED,
        )
        self.assertEqual('kleine Hunde', result)

    # ------------------------------------------------------------------
    # Word selection: stops after first noun, ignores words after it
    # ------------------------------------------------------------------

    def test_word_selection_stops_after_first_noun(self):
        # "kleine Gurke mit dem Sosse" — only "kleine" and "Gurke" should change
        result = DeDeclinator.declinate(
            'kleine Gurke mit dem Sosse',
            casus=DeCasus.DATIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.WEAK,
        )
        self.assertEqual('der kleinen Gurke mit dem Sosse', result)

    # ------------------------------------------------------------------
    # Punctuation handling
    # ------------------------------------------------------------------

    def test_punctuation_preserved(self):
        result = DeDeclinator.declinate(
            'frischer Kaffee, heiß',
            casus=DeCasus.GENITIV, numerus=DeNumerus.SINGULAR,
            article_type=DeArticleType.STRONG,
        )
        self.assertIn(',', result)

    # ------------------------------------------------------------------
    # No-op when no grammar specified
    # ------------------------------------------------------------------

    def test_no_grammar_unchanged(self):
        result = DeDeclinator.declinate('Hund')
        self.assertEqual('Hund', result)

    def test_empty_text(self):
        result = DeDeclinator.declinate('')
        self.assertEqual('', result)


if __name__ == '__main__':
    unittest.main()
