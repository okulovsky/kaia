import unittest
from grammatron.grammars.de import DeDeclinator, DeCasus, DeGenus, DeNumerus, DeArticleType, DePluralAgreement
from grammatron import Template, CardinalDub, OptionsDub, DubParameters, DeGrammarRule


class NounDeclinationTestCase(unittest.TestCase):
    def check(self, expected, vocabular, numerus, casus):
        prop = {
            DeCasus.NOMINATIV: "",
            DeCasus.GENITIV: "wegen ",
            DeCasus.DATIV: "mit ",
            DeCasus.AKKUSATIV: "für "
        }[casus]

        amount_value = 1 if numerus == DeNumerus.SINGULAR else 5

        amount = CardinalDub().as_variable('amount')
        template = Template(de=f"{prop}{DePluralAgreement(amount, vocabular)}")
        result = template.to_str(dict(amount = amount_value), DubParameters(language='de', grammar_rule=DeGrammarRule(casus=casus)))

        self.assertEqual(expected, result)

    def test_masc(self):
        v = "klein Hund"
        self.check("ein kleiner Hund",        v, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("wegen eines kleinen Hunds",  v, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("mit einem kleinen Hund",     v, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("für einen kleinen Hund",     v, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("fünf kleine Hunde",          v, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("wegen fünf kleiner Hunde",   v, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("mit fünf kleinen Hunden",    v, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("für fünf kleine Hunde",      v, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

    def test_fem(self):
        v = "klein Gurke"
        self.check("eine kleine Gurke",          v, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("wegen einer kleinen Gurke",  v, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("mit einer kleinen Gurke",    v, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("für eine kleine Gurke",      v, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("fünf kleine Gurken",         v, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("wegen fünf kleiner Gurken",  v, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("mit fünf kleinen Gurken",    v, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("für fünf kleine Gurken",     v, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)

    def test_neu(self):
        v = "klein Haus"
        self.check("ein kleines Haus",             v, DeNumerus.SINGULAR, DeCasus.NOMINATIV)
        self.check("wegen eines kleinen Hauses",   v, DeNumerus.SINGULAR, DeCasus.GENITIV)
        self.check("mit einem kleinen Haus",       v, DeNumerus.SINGULAR, DeCasus.DATIV)
        self.check("für ein kleines Haus",         v, DeNumerus.SINGULAR, DeCasus.AKKUSATIV)
        self.check("fünf kleine Häuser",           v, DeNumerus.PLURAL,   DeCasus.NOMINATIV)
        self.check("wegen fünf kleiner Häuser",    v, DeNumerus.PLURAL,   DeCasus.GENITIV)
        self.check("mit fünf kleinen Häusern",     v, DeNumerus.PLURAL,   DeCasus.DATIV)
        self.check("für fünf kleine Häuser",       v, DeNumerus.PLURAL,   DeCasus.AKKUSATIV)
