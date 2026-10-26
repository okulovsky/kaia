"""
The manifest of a speech dataset: a JSON line per utterance with
`audio` (the path relative to the manifest), `text` (as Nemotron writes it) and `language` (the model's locale).
No heavy imports: the dataset is built in the environment of Kaia, the model is trained in another one.
"""
import json
import re
from pathlib import Path

LOCALES = {'en': 'en-US', 'de': 'de-DE', 'ru': 'ru-RU'}


def as_model_writes(text: str) -> str:
    """Nemotron writes a capital letter and the final punctuation, and the training texts must be the same"""
    text = re.sub(r'\s+', ' ', text).strip()
    if text == '':
        return text
    text = text[0].upper() + text[1:]
    return text if text[-1] in '.!?' else text + '.'


def write(path: Path, records: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + '\n')


def read(path: Path) -> list[dict]:
    """The records with `audio` resolved to an absolute path"""
    path = Path(path)
    records = []
    for line in path.read_text().splitlines():
        if line.strip() == '':
            continue
        record = json.loads(line)
        record['audio'] = str((path.parent/record['audio']).resolve())
        records.append(record)
    return records


def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower())).strip()


def word_errors(expected: str, text: str) -> tuple[int, int]:
    """The word edit distance between the normalized texts, and the number of the expected words"""
    reference, hypothesis = normalize(expected).split(), normalize(text).split()
    previous = list(range(len(hypothesis) + 1))
    for i, r in enumerate(reference, 1):
        current = [i]
        for j, h in enumerate(hypothesis, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (r != h)))
        previous = current
    return previous[-1], len(reference)
