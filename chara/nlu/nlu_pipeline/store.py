import json
from pathlib import Path


class NluDatasetStore:
    """
    The text dataset of NLU, accumulated over the generation rounds.

    Every round is kept in `text-dataset/round-NNN.json`, and `text-dataset.json` is all the rounds together,
    in the format of TextDatasetPipeline, so everything that reads the dataset file keeps working.
    Repeated phrases are kept: the same phrase generated again is the evidence of how people say it,
    and the language model is trained on these frequencies.
    A `text-dataset.json` created before the rounds existed becomes the round 0, so it is not lost.
    """
    def __init__(self, folder: Path):
        self.folder = folder
        self.rounds_folder = folder / 'text-dataset'
        self.dataset_path = folder / 'text-dataset.json'
        self.negatives_path = folder / 'negatives.txt'

    def _round_path(self, number: int) -> Path:
        return self.rounds_folder / f'round-{number:03d}.json'

    def rounds(self) -> list[int]:
        if not self.rounds_folder.is_dir():
            return []
        return sorted(int(p.stem.split('-')[1]) for p in self.rounds_folder.glob('round-*.json'))

    def import_legacy_dataset(self) -> bool:
        """Turns the dataset file made before the rounds into the round 0; True if it happened."""
        if len(self.rounds()) > 0 or not self.dataset_path.is_file():
            return False
        self.write_round(0, json.loads(self.dataset_path.read_text()))
        return True

    def has_round(self, number: int) -> bool:
        return self._round_path(number).is_file()

    def write_round(self, number: int, records: list[dict]):
        self.rounds_folder.mkdir(parents=True, exist_ok=True)
        self._round_path(number).write_text(json.dumps(records, indent=2, ensure_ascii=False))
        self._write_union()

    def read(self) -> list[dict]:
        if not self.dataset_path.is_file():
            return []
        return json.loads(self.dataset_path.read_text())

    def read_negatives(self) -> list[str]:
        """Phrases that are not commands, one per line (e.g. made by NegativePipeline); empty if there are none"""
        if not self.negatives_path.is_file():
            return []
        return [line.strip() for line in self.negatives_path.read_text().splitlines() if line.strip()]

    def _write_union(self):
        records = []
        for number in self.rounds():
            records.extend(json.loads(self._round_path(number).read_text()))
        self.dataset_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
