"""Convert completed generation into a portable, feature-only dataset."""

import shutil
from pathlib import Path

from brainbox.deciders.voice_analysis.wakeword_training.runtime.archives import (
    write_archive,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import (
    read_json,
    sha256,
    write_json,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.manifests import (
    FILES,
    PARTS,
    identity,
    npy_header,
    validate_dataset,
)


def package_dataset(source):
    source = Path(source).resolve()
    data = source if source.name == "dataset" else source / "dataset"
    original = read_json(data / "manifest.json")
    if original.get("status") != "complete":
        raise ValueError("generation is incomplete")
    manifest = _build_manifest(data, original)
    report_path = data.parent / "report.json"
    report = read_json(report_path) if report_path.exists() else {}
    manifest["review_summary"] = {
        "groups": report.get("summary", {}),
        "rejection_reasons": report.get("rejection_reasons", {}),
    }
    manifest["corpus_id"] = identity(
        {key: value for key, value in manifest.items() if key != "corpus_id"}
    )
    portable = source.parent if source.name == "dataset" else source
    directory = portable / "portable-dataset"
    directory.mkdir(exist_ok=True)
    _copy_features(data, original, directory)
    write_json(directory / "manifest.json", manifest)
    validate_dataset(directory)
    archive = write_archive(
        portable / "dataset.zip",
        {name: directory / name for name in FILES},
    )
    return {
        "status": "complete",
        "dataset_folder": str(directory),
        "archive_path": str(archive),
        "archive_sha256": sha256(archive),
        "corpus_id": manifest["corpus_id"],
        "manifest_path": str(directory / "manifest.json"),
        "manifest_sha256": sha256(directory / "manifest.json"),
        "counts": {
            name: {
                "originals": part["accepted_original_count"],
                "rows": part["shape"][0],
            }
            for name, part in manifest["parts"].items()
        },
        "review_summary": manifest["review_summary"],
    }


def _build_manifest(data, original):
    config = original["settings"]
    resources = original["resources"]
    models = [
        {k: item[k] for k in ("id", "revision", "sha256") if k in item}
        for item in resources["resources"]
        if item["kind"] == "model"
    ]
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "target": {"name": config["name"], "variants": config["target_variants"]},
        "preparation": {
            k: v
            for k, v in config.items()
            if k not in ("resource_folder", "resource_specs")
        },
        "feature_space": {
            "shape": [16, 96],
            "dtype": "float32",
            "models": models,
            "recipe": "host-v2",
        },
        "lineage": original["lineage"],
        "parts": {},
    }
    for name in PARTS:
        info = original["artifacts"][name]
        path = (data / info["path"]).resolve()
        if not path.is_relative_to(data) or sha256(path) != info["sha256"]:
            raise ValueError("source feature integrity mismatch")
        label = name.split("_")[0]
        split = name.rsplit("_", 1)[1]
        count = sum(
            r["class_label"] == label and r["split"] == split
            for r in original["lineage"]
        )
        manifest["parts"][name] = {
            "file": name + ".npy",
            "sha256": sha256(path),
            "shape": npy_header(path),
            "accepted_original_count": count,
        }
    manifest["corpus_id"] = identity(manifest)
    return manifest


def _copy_features(data, original, directory):
    for name in PARTS:
        destination = directory / (name + ".npy")
        temporary = destination.with_suffix(".partial")
        shutil.copyfile(data / original["artifacts"][name]["path"], temporary)
        temporary.replace(destination)
