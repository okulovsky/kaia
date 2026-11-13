"""Atomic training metadata and content-addressed stage boundaries."""

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from ..generation.io import sha256
from ..generation.run_state import run_lock

__all__ = [
    "append_event",
    "artifact_hashes",
    "fingerprint",
    "history",
    "run_lock",
    "save_state",
    "verify_hashes",
]


def fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def save_state(path, state):
    import torch

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        torch.save(state, temp)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def append_event(root, event):
    with (Path(root) / "history.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, allow_nan=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def history(root):
    return [
        json.loads(x)
        for x in (Path(root) / "history.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def artifact_hashes(root, paths):
    return {str(Path(p).relative_to(root)): sha256(p) for p in paths}


def verify_hashes(root, hashes, allow_missing_report=False):
    root = Path(root)
    for name, expected in hashes.items():
        p = root / name
        if not p.resolve().is_relative_to(root.resolve()):
            raise ValueError("artifact path escapes output")
        if (
            allow_missing_report
            and name in ("report.html", "report_ru.html")
            and not p.exists()
        ):
            continue
        if not p.is_file() or sha256(p) != expected:
            raise ValueError(f"corrupted/missing training artifact: {name}")
