from dataclasses import dataclass
from ...data import CharacterReference, Character


@dataclass
class Side:
    character: Character
    is_protagonist: bool
    is_lead: bool


@dataclass
class Actors:
    protagonist: CharacterReference
    characters: CharacterReference
    opening: str|None = None
    length_factor: float = 1

    def get_sides(self, lead: CharacterReference) -> list[Side]:
        sides = []
        for character in self.characters + self.protagonist:
            sides.append(Side(
                character,
                character.name == self.protagonist.name,
                character in lead
            ))
        return sides

    def others(self, lead: CharacterReference) -> CharacterReference:
        return self.protagonist + self.characters - lead

    def all(self) -> CharacterReference:
        return self.protagonist + self.characters
