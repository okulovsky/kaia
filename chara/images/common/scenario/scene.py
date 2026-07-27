from dataclasses import dataclass
from .image_scenario import assemble_tags, convert_to_lists

@dataclass
class Scene:
    position: list[str]
    environment: list[str]

    def __post_init__(self):
        convert_to_lists(self)


    def to_prompt(self):
        return assemble_tags(
            self.position,
            self.environment
        )
