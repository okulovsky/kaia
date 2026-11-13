"""Resolve content-addressed inputs without downloading or repairing them."""

from contextvars import ContextVar
from pathlib import Path

import numpy as np

from ..generation.io import read_json, sha256

PARTS = tuple(
    f"{c}_features_{s}" for c in ("positive", "negative") for s in ("train", "test")
)
_opened = ContextVar("training_input_mmaps", default=None)


def checked_array(path, expected_hash, shape=None):
    path = Path(path).resolve()
    if not expected_hash or sha256(path) != expected_hash:
        raise ValueError(f"input hash mismatch: {path}")
    array = np.load(path, mmap_mode="r", allow_pickle=False)
    if _opened.get() is not None:
        _opened.get().append(array)
    if array.dtype.kind not in "fiu" or not array.size:
        raise ValueError(f"empty/non-real numeric input: {path}")
    if shape is not None and list(array.shape) != list(shape):
        raise ValueError(f"input shape mismatch: {path}")
    flat = array.reshape(-1, order="A")
    for offset in range(0, flat.size, 262144):
        chunk = flat[offset : offset + 262144]
        if not np.isfinite(chunk).all() or np.any(
            np.abs(chunk.astype(np.float64)) > np.finfo(np.float32).max
        ):
            raise ValueError(f"non-finite input: {path}")
    return array, {
        "file": str(path),
        "sha256": expected_hash,
        "size_bytes": path.stat().st_size,
        "actual_shape": list(array.shape),
        "dtype": str(array.dtype),
        "rows": len(array),
        "finite_check": True,
    }


def resolve_inputs(dataset, background_manifest=None):
    opened = []
    token = _opened.set(opened)
    try:
        return _resolve_inputs(dataset, background_manifest)
    except BaseException:
        for array in opened:
            mapping = getattr(array, "_mmap", None)
            if mapping is not None and not mapping.closed:
                mapping.close()
        raise
    finally:
        _opened.reset(token)


def _resolve_inputs(dataset, background_manifest=None):
    root = Path(dataset).resolve()
    data = (
        root
        if (root / "manifest.json").exists() and root.name == "dataset"
        else root / "dataset"
    )
    manifest_path = data / "manifest.json"
    manifest = read_json(manifest_path)
    if manifest.get("status") != "complete":
        raise ValueError("dataset manifest is not complete")
    arrays = {}
    parts = {}
    for name in PARTS:
        info = manifest["artifacts"][name]
        file = (data / info["path"]).resolve()
        if not file.is_relative_to(data.resolve()):
            raise ValueError("dataset artifact escapes dataset directory")
        array, meta = checked_array(file, info["sha256"], info.get("shape"))
        if array.ndim != 3 or array.shape[1:] != (16, 96):
            raise ValueError(f"{name}: expected nonempty (N,16,96)")
        if "dtype" in info and info["dtype"] != str(array.dtype):
            raise ValueError(f"{name}: dtype mismatch")
        meta.update(
            class_label=name.split("_")[0],
            role="train" if name.endswith("train") else "validation",
        )
        arrays[name] = array
        parts[name] = meta
    lineage = manifest.get("lineage", [])
    seen = {}
    for item in lineage:
        key = item["lineage_id"]
        split = item["split"]
        if key in seen and seen[key] != split:
            raise ValueError("lineage crosses train/validation splits")
        seen[key] = split
    resources_path = data.parent / "resources.json"
    resources = read_json(resources_path)
    if resources != manifest["resources"]:
        raise ValueError("dataset resources manifest mismatch")
    if background_manifest:
        bgpath = Path(background_manifest).resolve()
        bg = read_json(bgpath)
        if not bg.get("source_hashes"):
            raise ValueError("background manifest requires source_hashes")
        base = bgpath.parent
        tr = bg["train"]
        va = bg["validation"]
        train, tmeta = checked_array(base / tr["file"], tr["sha256"])
        val, vmeta = checked_array(base / va["file"], va["sha256"])
        lengths = va["segment_lengths"]
        frame = bg["frame_step_seconds"]
        provenance = {
            "manifest_path": str(bgpath),
            "sha256": sha256(bgpath),
            "source_hashes": bg["source_hashes"],
        }
    else:
        choices = [x for x in resources["resources"] if x["kind"] == "acav"]
        if len(choices) != 1:
            raise ValueError("expected exactly one provenanced ACAV resource")
        item = choices[0]
        if not item.get("sha256") or not item.get("revision"):
            raise ValueError("ACAV source provenance missing")
        base = Path(resources["resource_root"])
        tr = next(
            x for x in item["artifacts"] if Path(x["file"]).name == "acav_train.npy"
        )
        va = next(
            x for x in item["artifacts"] if Path(x["file"]).name == "acav_val.npy"
        )
        train, tmeta = checked_array(base / tr["file"], tr["sha256"])
        val, vmeta = checked_array(base / va["file"], va["sha256"])
        if train.ndim != 3 or val.ndim != 2 or len(val) % train.shape[1]:
            raise ValueError("ACAV validation segmentation cannot be proven")
        lengths = [train.shape[1]] * (len(val) // train.shape[1])
        frame = 0.08
        provenance = {k: item.get(k) for k in ("id", "revision", "sha256", "source")}
    if train.ndim != 3 or train.shape[1] < 16 or train.shape[2] != 96:
        raise ValueError("background train must be (N,T>=16,96)")
    if val.ndim == 3:
        if val.shape[-1] != 96:
            raise ValueError("background feature width must be 96")
        val = val.reshape(-1, 96)
    if val.ndim != 2 or val.shape[1] != 96:
        raise ValueError("background validation must be (M,96)")
    if (
        not lengths
        or any(type(x) is not int or x <= 0 for x in lengths)
        or sum(lengths) != len(val)
    ):
        raise ValueError("invalid segment lengths")
    if type(frame) not in (int, float) or not np.isfinite(frame) or frame != 0.08:
        raise ValueError("recipe requires proven frame_step_seconds=0.08")
    if tmeta["file"] == vmeta["file"] or tmeta["sha256"] == vmeta["sha256"]:
        raise ValueError("background train/validation must be separate")
    frames = sum(x for x in lengths if x >= 16)
    windows = sum(max(0, x - 15) for x in lengths)
    if not frames or not windows:
        raise ValueError("zero background exposure/windows")
    background = {
        "train": tmeta,
        "validation": vmeta,
        "segment_lengths": lengths,
        "frame_step_seconds": frame,
        "evaluated_frames": frames,
        "total_valid_windows": windows,
        "excluded_segments": sum(x < 16 for x in lengths),
        "feature_equivalent_hours": frames * frame / 3600,
        "waveform_hours": None,
        "provenance": provenance,
        "stride": 1,
    }
    snapshot = {
        "schema_version": 1,
        "dataset_manifest_path": str(manifest_path),
        "dataset_manifest_sha256": sha256(manifest_path),
        "resource_manifest_path": str(resources_path),
        "resource_manifest_sha256": sha256(resources_path),
        "generation_root": str(data.parent),
        "supervised_parts": parts,
        "background": background,
        "generation_settings": manifest["settings"],
        "lineage": lineage,
        "review_count": len(list((data.parent / "review").rglob("record.json"))),
        "unavailable_fields": {
            "waveform_hours": "not measured by feature generation",
            "speaker_count": "voice descriptions are not verified speaker identities",
        },
    }
    arrays.update(background_train=train, background_validation=val)
    return snapshot, arrays
