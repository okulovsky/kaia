from dataclasses import dataclass, fields
from .image_scenario import assemble_tags, convert_to_lists


@dataclass
class Clothing:
    top: list[str]|None = None
    bottom: list[str]|None = None
    costume: list[str]|None = None
    outerwear: list[str]|None = None
    footwear: list[str]|None = None
    headwear: list[str]|None = None
    accessories: list[str]|None = None

    def __post_init__(self):
        convert_to_lists(self)

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