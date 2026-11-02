"""
The manifest of a speech dataset: a JSON line per utterance with
`audio` (the path relative to the manifest), `text` (as Nemotron writes it) and `language` (the model's locale).
No heavy imports: the dataset is built in the environment of Kaia, the model is trained in another one.
"""
import json
import re
from pathlib import Path

LOCALES = {'en': 'en-US', 'de': 'de-DE', 'ru': 'ru-RU'}
# The model all the scripts work with
MODEL = 'nvidia/nemotron-3.5-asr-streaming-0.6b'
REVISION = 'ea30d66debe3740a08b573244286791d423d6b3e'
NEMO_FILE = 'nemotron-3.5-asr-streaming-0.6b.nemo'


def as_model_writes(text: str) -> str:
    """Nemotron writes a capital letter and the final punctuation, and the training texts must be the same.
    Some texts of the NLU dataset have the ** of a paraphrasing model."""
    text = re.sub(r'\s+', ' ', text.replace('**', '')).strip()
    if text == '':
        return text
    text = text[0].upper() + text[1:]
    return text if text[-1] in '.!?' else text + '.'


def transcript(record: dict) -> str:
    """What the model is trained to write: the text, and the tag of the language closing it"""
    return f"{record['text']} <{record['language']}>"


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
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', '', text.lower().replace('ё', 'е'))).strip()


def edit_distance(a, b) -> int:
    """Of two sequences: of words, or of the characters of a string"""
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def word_errors(expected: str, text: str) -> tuple[int, int]:
    """The word edit distance between the normalized texts, and the number of the expected words"""
    reference = normalize(expected).split()
    return edit_distance(reference, normalize(text).split()), len(reference)
