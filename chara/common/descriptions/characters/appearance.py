from dataclasses import dataclass
import random

@dataclass
class Appearance:
    clothing: str|None = None
    colors: str|None = None
    positive_prompt: str|None = None
    negative_prompt: str|None = None
    details: dict[str, list[str]]|None = None

    def get_random_details(self, key: str) -> str|None:
        if self.details is None:
            return None
        if key not in self.details:
            return None
        if len(self.details[key]) == 0:
            return None
        return random.choice(self.details[key])




