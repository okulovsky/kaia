from typing import *
from enum import Enum


class Gender(Enum):
    Feminine = 0
    Masculine = 1
    Neutral = 2


class Pronouns:
    @staticmethod
    def get(gender: Optional['Gender'], plural: bool, case: int):
        if plural:
            return ['they', 'them', 'their', 'themselves'][case]
        if gender == Gender.Feminine:
            return ['she', 'her', 'her', 'herself'][case]
        elif gender == Gender.Masculine:
            return ['he', 'him', 'his', 'himself'][case]
        else:
            return ['it', 'it', 'its', 'itself'][case]

    def __init__(self, gender: Optional['Gender'], plural: bool = False):
        self.gender = gender
        self.plural = plural

    @property
    def subjective(self):
        return Pronouns.get(self.gender, self.plural, 0)

    @property
    def objective(self):
        return Pronouns.get(self.gender, self.plural, 1)

    @property
    def possessive(self):
        return Pronouns.get(self.gender, self.plural, 2)

    @property
    def reflexive(self):
        return Pronouns.get(self.gender, self.plural, 3)


