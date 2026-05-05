import random
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict


@dataclass
class IntentUtterance:
    text: str
    intent: str
    language: str


def load_dataset(path: Path) -> list[IntentUtterance]:
    """Parses expanded dataset file into list of IntentUtterance."""
    utterances = []
    current_intent = None
    current_language = None

    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            parts = line[1:].strip().split('|')
            current_intent = parts[0].strip()
            current_language = parts[1].strip() if len(parts) > 1 else 'ru'
        else:
            if current_intent is not None:
                utterances.append(IntentUtterance(
                    text=line,
                    intent=current_intent,
                    language=current_language,
                ))

    return utterances


def load_negatives(path: Path, language: str = 'ru') -> list[str]:
    """Loads negatives file (one phrase per line)."""
    lines = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            lines.append(line)
    return lines


def train_test_split(
    utterances: list[IntentUtterance],
    test_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[list[IntentUtterance], list[IntentUtterance]]:
    """Stratified split: takes ~test_ratio from each intent into test."""
    by_intent = defaultdict(list)
    for u in utterances:
        by_intent[u.intent].append(u)

    rng = random.Random(seed)
    train, test = [], []

    for intent, items in by_intent.items():
        shuffled = items.copy()
        rng.shuffle(shuffled)
        n_test = max(1, int(len(shuffled) * test_ratio))
        test.extend(shuffled[:n_test])
        train.extend(shuffled[n_test:])

    return train, test
