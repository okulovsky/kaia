from dataclasses import dataclass


@dataclass(frozen=True)
class NegativeCase:
    language: str
    batch_index: int
