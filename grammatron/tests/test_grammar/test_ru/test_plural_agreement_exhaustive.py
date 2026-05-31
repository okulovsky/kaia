import unittest
from grammatron import CardinalDub, DubParameters
from grammatron.grammars.ru import RuPluralAgreement, RuCase


PARAMS = DubParameters(language='ru')


class RuPluralAgreementExhaustiveTestCase(unittest.TestCase):
    def check(self, expected, entity, amount, case=None):
        ag = RuPluralAgreement(CardinalDub().as_variable('amount'), entity)
        if case is not None:
            ag = ag.grammar.ru(case=case)
        result = ag.to_str(dict(amount=amount), PARAMS)
        self.assertEqual(expected, result)

    # --- маленький чемодан: masculine, inanimate ---

    def test_chemod_nom(self):
        e = 'маленький чемодан'
        self.check('один маленький чемодан',      e, 1)
        self.check('два маленьких чемодана',      e, 2)
        self.check('три маленьких чемодана',      e, 3)
        self.check('пять маленьких чемоданов',    e, 5)

    def test_chemod_gen(self):
        e = 'маленький чемодан'
        self.check('одного маленького чемодана',  e, 1, RuCase.GENITIVE)
        self.check('двух маленьких чемоданов',    e, 2, RuCase.GENITIVE)
        self.check('трёх маленьких чемоданов',    e, 3, RuCase.GENITIVE)
        self.check('пяти маленьких чемоданов',    e, 5, RuCase.GENITIVE)

    def test_chemod_dat(self):
        e = 'маленький чемодан'
        self.check('одному маленькому чемодану',  e, 1, RuCase.DATIVE)
        self.check('двум маленьким чемоданам',    e, 2, RuCase.DATIVE)
        self.check('трём маленьким чемоданам',    e, 3, RuCase.DATIVE)
        self.check('пяти маленьким чемоданам',    e, 5, RuCase.DATIVE)

    def test_chemod_acc(self):
        e = 'маленький чемодан'
        self.check('один маленький чемодан',      e, 1, RuCase.ACCUSATIVE)
        self.check('два маленьких чемодана',      e, 2, RuCase.ACCUSATIVE)
        self.check('три маленьких чемодана',      e, 3, RuCase.ACCUSATIVE)
        self.check('пять маленьких чемоданов',    e, 5, RuCase.ACCUSATIVE)

    def test_chemod_inst(self):
        e = 'маленький чемодан'
        self.check('одним маленьким чемоданом',   e, 1, RuCase.INSTRUMENTAL)
        self.check('двумя маленькими чемоданами', e, 2, RuCase.INSTRUMENTAL)
        self.check('тремя маленькими чемоданами', e, 3, RuCase.INSTRUMENTAL)
        self.check('пятью маленькими чемоданами', e, 5, RuCase.INSTRUMENTAL)

    # --- маленький слон: masculine, animate ---

    def test_slon_nom(self):
        e = 'маленький слон'
        self.check('один маленький слон',         e, 1)
        self.check('два маленьких слона',         e, 2)
        self.check('три маленьких слона',         e, 3)
        self.check('пять маленьких слонов',       e, 5)

    def test_slon_gen(self):
        e = 'маленький слон'
        self.check('одного маленького слона',     e, 1, RuCase.GENITIVE)
        self.check('двух маленьких слонов',       e, 2, RuCase.GENITIVE)
        self.check('трёх маленьких слонов',       e, 3, RuCase.GENITIVE)
        self.check('пяти маленьких слонов',       e, 5, RuCase.GENITIVE)

    def test_slon_dat(self):
        e = 'маленький слон'
        self.check('одному маленькому слону',     e, 1, RuCase.DATIVE)
        self.check('двум маленьким слонам',       e, 2, RuCase.DATIVE)
        self.check('трём маленьким слонам',       e, 3, RuCase.DATIVE)
        self.check('пяти маленьким слонам',       e, 5, RuCase.DATIVE)

    def test_slon_acc(self):
        e = 'маленький слон'
        self.check('одного маленького слона',     e, 1, RuCase.ACCUSATIVE)
        self.check('двух маленьких слонов',       e, 2, RuCase.ACCUSATIVE)
        self.check('трёх маленьких слонов',       e, 3, RuCase.ACCUSATIVE)
        self.check('пять маленьких слонов',       e, 5, RuCase.ACCUSATIVE)

    def test_slon_inst(self):
        e = 'маленький слон'
        self.check('одним маленьким слоном',      e, 1, RuCase.INSTRUMENTAL)
        self.check('двумя маленькими слонами',    e, 2, RuCase.INSTRUMENTAL)
        self.check('тремя маленькими слонами',    e, 3, RuCase.INSTRUMENTAL)
        self.check('пятью маленькими слонами',    e, 5, RuCase.INSTRUMENTAL)

    # --- маленький мужчина: masculine animate, 1st declension ---

    def test_muzhchina_nom(self):
        e = 'маленький мужчина'
        self.check('один маленький мужчина',      e, 1)
        self.check('два маленьких мужчины',       e, 2)
        self.check('три маленьких мужчины',       e, 3)
        self.check('пять маленьких мужчин',       e, 5)

    def test_muzhchina_gen(self):
        e = 'маленький мужчина'
        self.check('одного маленького мужчины',   e, 1, RuCase.GENITIVE)
        self.check('двух маленьких мужчин',       e, 2, RuCase.GENITIVE)
        self.check('трёх маленьких мужчин',       e, 3, RuCase.GENITIVE)
        self.check('пяти маленьких мужчин',       e, 5, RuCase.GENITIVE)

    def test_muzhchina_dat(self):
        e = 'маленький мужчина'
        self.check('одному маленькому мужчине',   e, 1, RuCase.DATIVE)
        self.check('двум маленьким мужчинам',     e, 2, RuCase.DATIVE)
        self.check('трём маленьким мужчинам',     e, 3, RuCase.DATIVE)
        self.check('пяти маленьким мужчинам',     e, 5, RuCase.DATIVE)

    def test_muzhchina_acc(self):
        e = 'маленький мужчина'
        self.check('одного маленького мужчину',   e, 1, RuCase.ACCUSATIVE)
        self.check('двух маленьких мужчин',       e, 2, RuCase.ACCUSATIVE)
        self.check('трёх маленьких мужчин',       e, 3, RuCase.ACCUSATIVE)
        self.check('пять маленьких мужчин',       e, 5, RuCase.ACCUSATIVE)

    def test_muzhchina_inst(self):
        e = 'маленький мужчина'
        self.check('одним маленьким мужчиной',    e, 1, RuCase.INSTRUMENTAL)
        self.check('двумя маленькими мужчинами',  e, 2, RuCase.INSTRUMENTAL)
        self.check('тремя маленькими мужчинами',  e, 3, RuCase.INSTRUMENTAL)
        self.check('пятью маленькими мужчинами',  e, 5, RuCase.INSTRUMENTAL)

    # --- маленькая стена: feminine, inanimate ---

    def test_stena_nom(self):
        e = 'маленькая стена'
        self.check('одна маленькая стена',        e, 1)
        self.check('две маленьких стены',         e, 2)
        self.check('три маленьких стены',         e, 3)
        self.check('пять маленьких стен',         e, 5)

    def test_stena_gen(self):
        e = 'маленькая стена'
        self.check('одной маленькой стены',       e, 1, RuCase.GENITIVE)
        self.check('двух маленьких стен',         e, 2, RuCase.GENITIVE)
        self.check('трёх маленьких стен',         e, 3, RuCase.GENITIVE)
        self.check('пяти маленьких стен',         e, 5, RuCase.GENITIVE)

    def test_stena_dat(self):
        e = 'маленькая стена'
        self.check('одной маленькой стене',       e, 1, RuCase.DATIVE)
        self.check('двум маленьким стенам',       e, 2, RuCase.DATIVE)
        self.check('трём маленьким стенам',       e, 3, RuCase.DATIVE)
        self.check('пяти маленьким стенам',       e, 5, RuCase.DATIVE)

    def test_stena_acc(self):
        e = 'маленькая стена'
        self.check('одну маленькую стену',        e, 1, RuCase.ACCUSATIVE)
        self.check('две маленьких стены',         e, 2, RuCase.ACCUSATIVE)
        self.check('три маленьких стены',         e, 3, RuCase.ACCUSATIVE)
        self.check('пять маленьких стен',         e, 5, RuCase.ACCUSATIVE)

    def test_stena_inst(self):
        e = 'маленькая стена'
        self.check('одной маленькой стеной',      e, 1, RuCase.INSTRUMENTAL)
        self.check('двумя маленькими стенами',    e, 2, RuCase.INSTRUMENTAL)
        self.check('тремя маленькими стенами',    e, 3, RuCase.INSTRUMENTAL)
        self.check('пятью маленькими стенами',    e, 5, RuCase.INSTRUMENTAL)

    # --- маленькая мышь: feminine, animate ---

    def test_mysh_nom(self):
        e = 'маленькая мышь'
        self.check('одна маленькая мышь',         e, 1)
        self.check('две маленьких мыши',          e, 2)
        self.check('три маленьких мыши',          e, 3)
        self.check('пять маленьких мышей',        e, 5)

    def test_mysh_gen(self):
        e = 'маленькая мышь'
        self.check('одной маленькой мыши',        e, 1, RuCase.GENITIVE)
        self.check('двух маленьких мышей',        e, 2, RuCase.GENITIVE)
        self.check('трёх маленьких мышей',        e, 3, RuCase.GENITIVE)
        self.check('пяти маленьких мышей',        e, 5, RuCase.GENITIVE)

    def test_mysh_dat(self):
        e = 'маленькая мышь'
        self.check('одной маленькой мыши',        e, 1, RuCase.DATIVE)
        self.check('двум маленьким мышам',        e, 2, RuCase.DATIVE)
        self.check('трём маленьким мышам',        e, 3, RuCase.DATIVE)
        self.check('пяти маленьким мышам',        e, 5, RuCase.DATIVE)

    def test_mysh_acc(self):
        e = 'маленькая мышь'
        self.check('одну маленькую мышь',         e, 1, RuCase.ACCUSATIVE)
        self.check('двух маленьких мышей',        e, 2, RuCase.ACCUSATIVE)
        self.check('трёх маленьких мышей',        e, 3, RuCase.ACCUSATIVE)
        self.check('пять маленьких мышей',        e, 5, RuCase.ACCUSATIVE)

    def test_mysh_inst(self):
        e = 'маленькая мышь'
        self.check('одной маленькой мышью',       e, 1, RuCase.INSTRUMENTAL)
        self.check('двумя маленькими мышами',     e, 2, RuCase.INSTRUMENTAL)
        self.check('тремя маленькими мышами',     e, 3, RuCase.INSTRUMENTAL)
        self.check('пятью маленькими мышами',     e, 5, RuCase.INSTRUMENTAL)

    # --- маленькое окно: neuter, inanimate ---

    def test_okno_nom(self):
        e = 'маленькое окно'
        self.check('одно маленькое окно',         e, 1)
        self.check('два маленьких окна',          e, 2)
        self.check('три маленьких окна',          e, 3)
        self.check('пять маленьких окон',         e, 5)

    def test_okno_gen(self):
        e = 'маленькое окно'
        self.check('одного маленького окна',      e, 1, RuCase.GENITIVE)
        self.check('двух маленьких окон',         e, 2, RuCase.GENITIVE)
        self.check('трёх маленьких окон',         e, 3, RuCase.GENITIVE)
        self.check('пяти маленьких окон',         e, 5, RuCase.GENITIVE)

    def test_okno_dat(self):
        e = 'маленькое окно'
        self.check('одному маленькому окну',      e, 1, RuCase.DATIVE)
        self.check('двум маленьким окнам',        e, 2, RuCase.DATIVE)
        self.check('трём маленьким окнам',        e, 3, RuCase.DATIVE)
        self.check('пяти маленьким окнам',        e, 5, RuCase.DATIVE)

    def test_okno_acc(self):
        e = 'маленькое окно'
        self.check('одно маленькое окно',         e, 1, RuCase.ACCUSATIVE)
        self.check('два маленьких окна',          e, 2, RuCase.ACCUSATIVE)
        self.check('три маленьких окна',          e, 3, RuCase.ACCUSATIVE)
        self.check('пять маленьких окон',         e, 5, RuCase.ACCUSATIVE)

    def test_okno_inst(self):
        e = 'маленькое окно'
        self.check('одним маленьким окном',       e, 1, RuCase.INSTRUMENTAL)
        self.check('двумя маленькими окнами',     e, 2, RuCase.INSTRUMENTAL)
        self.check('тремя маленькими окнами',     e, 3, RuCase.INSTRUMENTAL)
        self.check('пятью маленькими окнами',     e, 5, RuCase.INSTRUMENTAL)
