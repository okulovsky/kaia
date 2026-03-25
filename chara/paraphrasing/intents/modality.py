from dataclasses import dataclass


@dataclass
class Modality:
    name: str
    description: str


MODALITIES = [
    Modality('neutral', 'speaks neutrally and clearly'),
    Modality('quick', 'speaks quickly and briefly, no filler words'),
]
