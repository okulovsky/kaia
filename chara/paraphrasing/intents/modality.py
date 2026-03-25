from dataclasses import dataclass


@dataclass
class Modality:
    name: str
    description: str


MODALITIES = [
    Modality('neutral', 'говорит нейтрально и чётко'),
    Modality('quick', 'говорит быстро и коротко, без лишних слов'),
]
