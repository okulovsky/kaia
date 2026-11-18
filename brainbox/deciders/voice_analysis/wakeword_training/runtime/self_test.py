"""Synthetic numeric corpus for the controller's transport/native self-test."""

import struct
from pathlib import Path

from .archives import write_archive
from .io import sha256, write_json
from .manifests import FILES, PARTS, identity, validate_dataset


def create_self_test_dataset(folder, feature_space):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "target": {"name": "synthetic-self-test", "variants": ["synthetic-self-test"]},
        "preparation": {"origin": "controller synthetic numeric self-test, no audio"},
        "feature_space": feature_space,
        "lineage": [],
        "parts": {},
    }
    for index, name in enumerate(PARTS):
        path = folder / (name + ".npy")
        _write_features(path, float(index) / 10)
        label, _, split = name.split("_")
        manifest["lineage"].extend(
            {
                "lineage_id": f"{name}-{i}",
                "sample_id": f"{name}-{i}",
                "class_label": label,
                "split": split,
            }
            for i in range(3)
        )
        manifest["parts"][name] = {
            "file": path.name,
            "sha256": sha256(path),
            "shape": [3, 16, 96],
            "accepted_original_count": 3,
        }
    manifest["corpus_id"] = identity(manifest)
    write_json(folder / "manifest.json", manifest)
    validate_dataset(folder)
    return write_archive(
        folder.parent / "dataset.zip", {name: folder / name for name in FILES}
    )


def _write_features(path, value):
    header = repr(
        {"descr": "<f4", "fortran_order": False, "shape": (3, 16, 96)}
    ).encode("ascii")
    header += b" " * ((64 - (10 + len(header) + 1) % 64) % 64) + b"\n"
    with path.open("wb") as output:
        output.write(b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header)
        output.write(struct.pack("<f", value) * (3 * 16 * 96))
