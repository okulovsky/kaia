"""Portable feature validation without a local ML stack."""

import ast
import hashlib
import json
import math
import struct
from array import array
from pathlib import Path

from .io import read_json, sha256

PARTS = tuple(
    f"{c}_features_{s}" for c in ("positive", "negative") for s in ("train", "test")
)
FILES = {"manifest.json", *(name + ".npy" for name in PARTS)}


def identity(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def normalized(values):
    if (
        not isinstance(values, list)
        or not values
        or any(not isinstance(v, str) or not v.strip() for v in values)
    ):
        raise ValueError("nonempty target variants required")
    return sorted({" ".join(v.casefold().split()) for v in values})


def npy_header(path, finite=True):
    import sys

    with Path(path).open("rb") as stream:
        if stream.read(6) != b"\x93NUMPY":
            raise ValueError("invalid NPY magic")
        version = stream.read(2)
        if version not in (b"\x01\x00", b"\x02\x00", b"\x03\x00"):
            raise ValueError("unsupported NPY version")
        size = struct.unpack(
            "<H" if version[0] == 1 else "<I", stream.read(2 if version[0] == 1 else 4)
        )[0]
        if size > 65536:
            raise ValueError("NPY header too large")
        header = ast.literal_eval(
            stream.read(size).decode("utf-8" if version[0] == 3 else "latin1")
        )
        shape = header["shape"]
        dtype = header["descr"]
        if (
            not isinstance(shape, tuple)
            or len(shape) != 3
            or shape[1:] != (16, 96)
            or type(shape[0]) is not int
            or shape[0] <= 0
            or dtype not in ("<f4", ">f4", "=f4")
        ):
            raise ValueError("expected float32 (N,16,96)")
        if Path(path).stat().st_size - stream.tell() != math.prod(shape) * 4:
            raise ValueError("NPY byte size mismatch")
        if finite:
            while chunk := stream.read(262144 * 4):
                values = array("f")
                values.frombytes(chunk)
                if (dtype[0] == ">" and sys.byteorder == "little") or (
                    dtype[0] == "<" and sys.byteorder == "big"
                ):
                    values.byteswap()
                if not all(math.isfinite(v) for v in values):
                    raise ValueError("non-finite features")
    return list(shape)


def validate_dataset(folder, requirements=None):
    if requirements:
        minimum = requirements.get("minimum_positive_counts", {})
        if set(minimum) != {"train", "validation"} or any(
            type(v) is not int or v <= 0 for v in minimum.values()
        ):
            raise ValueError("invalid positive count requirements")
    folder = Path(folder)
    m = read_json(folder / "manifest.json")
    if (
        m.get("schema_version") != 1
        or m.get("status") != "complete"
        or set(m.get("parts", {})) != set(PARTS)
    ):
        raise ValueError("invalid portable dataset schema")
    content = {k: v for k, v in m.items() if k != "corpus_id"}
    if identity(content) != m["corpus_id"]:
        raise ValueError("corpus identity mismatch")
    if requirements and requirements.get("corpus_id", m["corpus_id"]) != m["corpus_id"]:
        raise ValueError("uploaded corpus identity mismatch")
    variants = normalized(m["target"]["variants"])
    if requirements and variants != normalized(requirements["target_variants"]):
        raise ValueError("wakeword mismatch")
    seen = {}
    seen_samples = set()
    counts = {name: 0 for name in PARTS}
    for record in m["lineage"]:
        key = record["lineage_id"]
        split = record["split"]
        label = record["class_label"]
        part = f"{label}_features_{split}"
        sample_id = record.get("sample_id", key)
        if (
            part not in counts
            or not isinstance(key, str)
            or not key
            or not isinstance(sample_id, str)
            or not sample_id
            or key in seen
            or sample_id in seen_samples
            or record.get("review")
        ):
            raise ValueError("review/duplicate or cross-split lineage")
        seen_samples.add(sample_id)
        seen[key] = split
        counts[part] += 1
    for name in PARTS:
        info = m["parts"][name]
        path = folder / (name + ".npy")
        if (
            not path.resolve().is_relative_to(folder.resolve())
            or info["file"] != path.name
            or sha256(path) != info["sha256"]
        ):
            raise ValueError("feature hash/path mismatch")
        shape = npy_header(path)
        if (
            shape != info["shape"]
            or shape[0] < counts[name]
            or info["accepted_original_count"] != counts[name]
            or not counts[name]
        ):
            raise ValueError("feature shape/original count mismatch")
        if requirements and name.startswith("positive"):
            split = "train" if name.endswith("train") else "validation"
            if counts[name] < requirements["minimum_positive_counts"][split]:
                raise ValueError("insufficient positive samples: " + split)
    return m
