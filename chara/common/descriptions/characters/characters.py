from typing import *
from dataclasses import dataclass
from enum import Enum
from copy import copy

class Pronouns:
    @staticmethod
    def get(gender: Optional['Character.Gender'], plural: bool, case: int):
        if plural:
            return ['they', 'them', 'their', 'themselves'][case]
        if gender == Character.Gender.Feminine:
            return ['she', 'her', 'her', 'herself'][case]
        elif gender == Character.Gender.Masculine:
            return ['he', 'him', 'his', 'himself'][case]
        else:
            return ['it', 'it', 'its', 'itself'][case]

    def __init__(self, gender: Optional['Character.Gender'], plural: bool = False):
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


class Gender(Enum):
    Feminine = 0
    Masculine = 1
    Neutral = 2

class Entity:
    def __init__(self, name: str, description: str|None = None):
        self.name = name
        self.description = description
        self.gender = Gender.Neutral

    @property
    def pronoun(self):
        return Pronouns(self.gender, False)

    def __add__(self, other) -> 'CharacterSet':
        if isinstance(other, Entity):
            return CharacterSet((self,other))
        elif isinstance(other, CharacterSet):
            return CharacterSet((self,)+other.characters)
        else:
            raise ValueError("other should be Character or CharacterSet")

    def __str__(self):
        return self.name


class Character(Entity):
    Gender = Gender

    def __init__(self, name: str, gender: Gender, description: str|None):
        super().__init__(name, description)
        self.gender = gender


class EntitySet:
    def __init__(self, characters: Iterable[Entity]):
        self.characters = tuple(characters)
        self.junction = 'and'

    def with_junction(self, junction: str):
        result = copy(self)
        result.junction = junction
        return result

    def __add__(self, other) -> 'EntitySet':
        if isinstance(other, Entity):
            return EntitySet(self.characters+(other,))
        elif isinstance(other, EntitySet):
            return EntitySet(self.characters+other.characters)
        else:
            raise ValueError("Other should be Character or CharacterSet")

    def __str__(self):
        names = [c.name for c in self.characters]
        if len(names) > 1:
            return ', '.join(names[:-1]) + ' ' + self.junction + ' ' + names[-1]
        elif len(names) == 1:
            return names[0]
        else:
            raise ValueError("Empty character set")

    def __len__(self):
        return len(self.characters)

    def __index__(self, index: int) -> "Entity":
        return self.characters[index]

    def __iter__(self):
        return iter(self.characters)

    @property
    def pronoun(self):
        if len(self.characters) > 1:
            return Pronouns(None, True)
        elif len(self.characters) == 0:
            raise ValueError("Empty character set")
        else:
            return Pronouns(self.characters[0].gender, False)

CharacterSet = EntitySet