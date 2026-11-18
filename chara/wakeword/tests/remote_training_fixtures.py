"""Portable fixtures contain only synthetic numeric data, never downloaded audio."""

from pathlib import Path

from training_fixtures import dataset_fixture

from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
    read_json,
    write_json,
)
from chara.wakeword.generation.packaging import package_dataset


def portable_fixture(root):
    source = dataset_fixture(Path(root))
    path = source / "dataset/manifest.json"
    manifest = read_json(path)
    manifest["lineage"] = [
        {
            "lineage_id": f"{label}-{split}-{index}",
            "sample_id": f"{label}-{split}-{index}",
            "class_label": label,
            "split": split,
        }
        for label in ("positive", "negative")
        for split in ("train", "test")
        for index in range(3)
    ]
    write_json(path, manifest)
    return Path(package_dataset(source)["dataset_folder"])
