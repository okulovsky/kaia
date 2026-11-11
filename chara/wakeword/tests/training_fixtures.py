"""Small synthetic numeric inputs for tests, never production measurements."""

from pathlib import Path

import numpy as np
from chara.wakeword.generation.io import sha256, write_json


def dataset_fixture(root):
    root = Path(root)
    data = root / "dataset"
    data.mkdir(parents=True)
    rng = np.random.default_rng(11)
    artifacts = {}
    for label in ("positive", "negative"):
        for split in ("train", "test"):
            name = f"{label}_features_{split}"
            path = data / (name + ".npy")
            array = rng.normal(
                1 if label == "positive" else -1, 0.3, (3, 16, 96)
            ).astype("float32")
            np.save(path, array)
            artifacts[name] = {
                "path": path.name,
                "sha256": sha256(path),
                "shape": list(array.shape),
                "dtype": str(array.dtype),
            }
    folder = root / "resources"
    folder.mkdir()
    entries = []
    for name, shape in [("acav_train", (3, 20, 96)), ("acav_val", (40, 96))]:
        p = folder / (name + ".npy")
        np.save(p, rng.normal(-1, 0.3, shape).astype("float32"))
        entries.append({"file": p.name, "sha256": sha256(p)})
    resources = {
        "resource_root": str(folder.resolve()),
        "resources": [
            {
                "id": "fixture-acav",
                "kind": "acav",
                "revision": "test",
                "sha256": "fixture",
                "artifacts": entries,
            }
        ],
    }
    write_json(root / "resources.json", resources)
    write_json(
        data / "manifest.json",
        {
            "status": "complete",
            "artifacts": artifacts,
            "settings": {
                "name": "fixture",
                "target_variants": ["fixture"],
                "counts": {},
            },
            "resources": resources,
            "lineage": [],
        },
    )
    return root
