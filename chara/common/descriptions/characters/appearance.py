from dataclasses import dataclass

@dataclass
class Appearance:
    clothing: str|None = None
    colors: str|None = None
    positive_prompt: str|None = None
    negative_prompt: str|None = None
    outfits: dict[str, list[str]]|None = None

