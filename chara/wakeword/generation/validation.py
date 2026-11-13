from dataclasses import asdict
from pathlib import Path

from .dto import FeatureArtifact
from .io import read_json, sha256, write_json

FEATURES = (
    "positive_features_train",
    "negative_features_train",
    "positive_features_test",
    "negative_features_test",
)


def validate_lineage(lineage, settings):
    from collections import Counter

    groups = {}
    seen = set()
    counts = Counter()
    for item in lineage:
        if item["class_label"] not in ("positive", "negative") or item["split"] not in (
            "train",
            "test",
        ):
            raise ValueError("invalid lineage group")
        group = item["class_label"] + "_" + item["split"]
        identity = item["sample_id"]
        parent = item.get("lineage_id", identity)
        if (
            item.get("review")
            or identity in seen
            or parent in groups
            and groups[parent] != group
        ):
            raise ValueError("review/duplicate/lineage split contamination")
        seen.add(identity)
        groups[parent] = group
        counts[group] += 1
    if settings.get("counts") and dict(counts) != settings["counts"]:
        raise ValueError("source counts do not match the requested dataset")


def inspect_features(path):
    import numpy as np

    path = Path(path)
    array = np.load(path, mmap_mode="r", allow_pickle=False)
    if array.ndim != 3 or array.shape[1:] != (16, 96) or len(array) == 0:
        raise ValueError(f"invalid feature shape: {path}: {array.shape}")
    if array.dtype.kind not in "fiu":
        raise ValueError(f"invalid feature dtype: {path}")
    for start in range(0, len(array), 1024):
        if not np.isfinite(array[start : start + 1024]).all():
            raise ValueError(f"nonfinite features: {path}")
    result = FeatureArtifact(
        path.name,
        tuple(array.shape),
        str(array.dtype),
        sha256(path),
        path.stat().st_size,
    )
    del array
    return result


def publish_manifest(folder, settings, resources, lineage):
    folder = Path(folder)
    # Inspect every output before publishing a completion marker.
    artifacts = {name: inspect_features(folder / (name + ".npy")) for name in FEATURES}
    validate_lineage(lineage, settings)
    manifest = {
        "status": "complete",
        "settings": settings,
        "resources": resources,
        "artifacts": {k: asdict(v) for k, v in artifacts.items()},
        "lineage": lineage,
    }
    write_json(folder / "manifest.json", manifest)
    return artifacts


def check_completed(folder):
    folder = Path(folder)
    manifest = read_json(folder / "manifest.json")
    if manifest.get("status") != "complete" or set(manifest["artifacts"]) != set(
        FEATURES
    ):
        raise ValueError("incomplete dataset manifest")
    validate_lineage(manifest["lineage"], manifest["settings"])
    for name in FEATURES:
        expected = manifest["artifacts"][name]
        actual = asdict(inspect_features(folder / (name + ".npy")))
        actual["shape"] = list(actual["shape"])
        if actual != expected:
            raise ValueError(f"damaged artifact: {name}")
    return manifest
