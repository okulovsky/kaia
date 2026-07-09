from dataclasses import dataclass
from .appearance import Appearance
from .pronouns import Pronouns, Gender
from typing import ClassVar

@dataclass
class Character:
    name: str
    gender: Gender
    description: str
    appearance: Appearance|None = None

    Gender: ClassVar = Gender
    Appearance: ClassVar = Appearance

    @property
    def pronoun(self) -> Pronouns:
        return Pronouns(self.gender, False)

    def __str__(self) -> str:
        return self.name


