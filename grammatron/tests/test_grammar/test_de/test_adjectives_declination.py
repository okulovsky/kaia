import unittest
from grammatron.grammars.de import DeDeclinator, DeCasus, DeGenus, DeNumerus, DeArticleType


class AdjectiveDeclinationTestCase(unittest.TestCase):
    def check(self, expected, vocabular, article_type, numerus, casus):
        self.assertEqual(expected,
                         DeDeclinator.declinate(vocabular, casus=casus, numerus=numerus, article_type=article_type)
                         )

    def test_masc(self):
        v = "klein Hund"
        self.check("kleiner Hund",        v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("kleinen Hunds",       v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("kleinem Hund",        v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("kleinen Hund",        v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("kleine Hunde",        v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("kleiner Hunde",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("kleinen Hunden",      v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("kleine Hunde",        v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("der kleine Hund",     v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("des kleinen Hunds",   v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("dem kleinen Hund",    v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("den kleinen Hund",    v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("die kleinen Hunde",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("der kleinen Hunde",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("den kleinen Hunden",  v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("die kleinen Hunde",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("ein kleiner Hund",    v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("eines kleinen Hunds", v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("einem kleinen Hund",  v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("einen kleinen Hund",  v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("kleine Hunde",        v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("kleiner Hunde",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("kleinen Hunden",      v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("kleine Hunde",        v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

    def test_neu(self):
        v = "klein Haus"
        self.check("kleines Haus",         v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("kleinen Hauses",       v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("kleinem Haus",         v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("kleines Haus",         v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("kleine Häuser",        v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("kleiner Häuser",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("kleinen Häusern",      v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("kleine Häuser",        v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("das kleine Haus",      v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("des kleinen Hauses",   v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("dem kleinen Haus",     v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("das kleine Haus",      v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("die kleinen Häuser",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("der kleinen Häuser",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("den kleinen Häusern",  v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("die kleinen Häuser",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("ein kleines Haus",     v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("eines kleinen Hauses", v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("einem kleinen Haus",   v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("ein kleines Haus",     v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("kleine Häuser",        v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("kleiner Häuser",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("kleinen Häusern",      v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("kleine Häuser",        v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

    def test_fem(self):
        v = "klein Gurke"
        self.check("kleine Gurke",         v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("kleiner Gurke",        v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("kleiner Gurke",        v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("kleine Gurke",         v, DeArticleType.STRONG, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("kleine Gurken",        v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("kleiner Gurken",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("kleinen Gurken",       v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("kleine Gurken",        v, DeArticleType.STRONG, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("die kleine Gurke",     v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("der kleinen Gurke",    v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("der kleinen Gurke",    v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("die kleine Gurke",     v, DeArticleType.WEAK,   DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("die kleinen Gurken",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("der kleinen Gurken",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("den kleinen Gurken",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("die kleinen Gurken",   v, DeArticleType.WEAK,   DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

        self.check("eine kleine Gurke",    v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("einer kleinen Gurke",  v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("einer kleinen Gurke",  v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("eine kleine Gurke",    v, DeArticleType.MIXED,  DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("kleine Gurken",        v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("kleiner Gurken",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("kleinen Gurken",       v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("kleine Gurken",        v, DeArticleType.MIXED,  DeNumerus.PLURAL,   DeCasus.AKKUSATIV)
