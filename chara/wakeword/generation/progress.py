from pathlib import Path
from uuid import uuid4

from .io import read_json, write_json


class IncompleteGeneration(RuntimeError):
    pass


class AttemptLedger:
    """Single-writer ledger; run-level lock is required by the caller."""

    def __init__(self, folder, target, group=None):
        self.path = Path(folder) / "progress.json"
        self.target = target
        label, split = group.rsplit("_", 1) if group else (None, None)
        self.data = (
            read_json(self.path)
            if self.path.exists()
            else {
                "target": target,
                "group": group,
                "class_label": label,
                "split": split,
                "attempts": [],
            }
        )
        if (
            self.data.get("group") != group
            or self.data["target"] != target
            or len(self.data["attempts"]) > 3 * target
        ):
            raise ValueError("incompatible generation progress")
        ids = [item["sample_id"] for item in self.data["attempts"]]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate attempt identity in generation progress")

    def reserve(self, seed):
        return self.reserve_many([seed])[0]

    def reserve_many(self, seeds):
        if len(self.data["attempts"]) + len(seeds) > 3 * self.target:
            raise IncompleteGeneration("generation budget exhausted")
        output = []
        for seed in seeds:
            item = {
                "sample_id": uuid4().hex,
                "seed": seed,
                "task_id": uuid4().hex,
                "state": "planned",
                "index": len(self.data["attempts"]),
                "class_label": self.data["class_label"],
                "split": self.data["split"],
            }
            self.data["attempts"].append(item)
            output.append(item)
        self.save()
        return output

    def save(self):
        write_json(self.path, self.data)
