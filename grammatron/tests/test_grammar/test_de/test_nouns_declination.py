import unittest
from grammatron.grammars.de import DeDeclinator, DeCasus, DeGenus, DeNumerus, DeArticleType


class NounDeclinationTestCase(unittest.TestCase):
    def check(self, expected, vocabular, article_type, numerus, casus):
        self.assertEqual(expected,
                         DeDeclinator.declinate(vocabular, casus = casus, numerus = numerus, article_type = article_type)
                         )

    def test_masc(self):
        v = "Hund"
        self.check("Hund",        v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("Hunds",       v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("Hund",        v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("Hund",        v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("Hunde",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("Hunde",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("Hunden",      v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("Hunde",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("der Hund",    v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("des Hunds",   v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("dem Hund",    v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("den Hund",    v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("die Hunde",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("der Hunde",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("den Hunden",  v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("die Hunde",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("ein Hund",    v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("eines Hunds", v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("einem Hund",  v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("einen Hund",  v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("Hunde",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("Hunde",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("Hunden",      v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("Hunde",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

    def test_fem(self):
        v = 'Gurke'
        self.check("Gurke",       v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("Gurke",       v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("Gurke",       v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("Gurke",       v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("Gurken",      v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("Gurken",      v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("Gurken",      v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("Gurken",      v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("die Gurke",   v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("der Gurke",   v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("der Gurke",   v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("die Gurke",   v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("die Gurken",  v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("der Gurken",  v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("den Gurken",  v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("die Gurken",  v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("eine Gurke",  v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("einer Gurke", v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("einer Gurke", v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("eine Gurke",  v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("Gurken",      v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("Gurken",      v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("Gurken",      v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("Gurken",      v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

    def test_neu(self):
        v = 'Haus'
        self.check("Haus",         v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("Hauses",       v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("Haus",         v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("Haus",         v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("Häuser",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("Häuser",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("Häusern",      v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("Häuser",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("das Haus",     v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("des Hauses",   v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("dem Haus",     v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("das Haus",     v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("die Häuser",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("der Häuser",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("den Häusern",  v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("die Häuser",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("ein Haus",     v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("eines Hauses", v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("einem Haus",   v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("ein Haus",     v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("Häuser",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("Häuser",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("Häusern",      v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("Häuser",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.AKKUSATIV)
