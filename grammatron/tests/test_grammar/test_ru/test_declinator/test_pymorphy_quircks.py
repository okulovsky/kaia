from unittest import TestCase
from grammatron.grammars.ru import *

import unittest

class TestPymorphyQuirks(unittest.TestCase):
    def test_dva(self):
        self.assertEqual('двумя', Declinator.inflect_word('два', gender=RuGender.FEMININE, case = RuDeclension.INSTRUMENTAL))