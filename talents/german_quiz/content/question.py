from dataclasses import dataclass

@dataclass
class Question:
    id: str
    answer: str
    topic: str
    genus: list[str]
    plural: list[str]
    question: str