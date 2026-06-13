from dataclasses import dataclass
from ...common import assemble_tags

@dataclass
class Clothing:
    top: list[str]|None = None
    bottom: list[str]|None = None
    costume: list[str]|None = None
    outerwear: list[str]|None = None
    footwear: list[str]|None = None
    headwear: list[str]|None = None
    accessories: list[str]|None = None

    def to_prompt(self):
        return assemble_tags(
            self.top,
            self.bottom,
            self.costume,
            self.outerwear,
            self.footwear,
            self.headwear,
            self.accessories
        )