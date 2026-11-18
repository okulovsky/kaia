"""Immutable server exports and independently derived local reports."""

from pathlib import Path

from .archives import write_archive
from .io import read_json, sha256, write_json
from .state import verify_hashes

PRIMARY = (
    "config.json",
    "data-snapshot.json",
    "history.jsonl",
    "checkpoint-selection.json",
    "export-check.json",
    "metrics.json",
    "scores/positive_validation.npy",
    "scores/negative_validation.npy",
    "scores/background_validation.npy",
    "report.html",
    "report_ru.html",
)


def package_result(root, training_id, request_fingerprint):
    root = Path(root)
    config = read_json(root / "config.json")
    names = [*PRIMARY, config["model_name"] + ".onnx"]
    hashes = {name: sha256(root / name) for name in names}
    manifest = {
        "schema_version": 1,
        "status": "complete",
        "training_id": training_id,
        "run_id": read_json(root / "state.json")["run_id"],
        "request_fingerprint": request_fingerprint,
        "execution_fingerprint": read_json(root / "state.json")["fingerprint"],
        "hashes": hashes,
    }
    write_json(root / "result-manifest.json", manifest)
    archive = root / "result.zip"
    write_archive(
        archive,
        {
            **{name: root / name for name in names},
            "result-manifest.json": root / "result-manifest.json",
        },
    )
    return {
        "training_id": training_id,
        "status": "complete",
        "request_fingerprint": request_fingerprint,
        "execution_fingerprint": read_json(root / "state.json")["fingerprint"],
        "result_manifest_sha256": sha256(root / "result-manifest.json"),
        "archive_sha256": sha256(archive),
        "archive_size": archive.stat().st_size,
        "model_sha256": hashes[config["model_name"] + ".onnx"],
    }


def verify_result(root, reference=None, allow_missing_reports=False):
    root = Path(root)
    m = read_json(root / "result-manifest.json")
    if m.get("schema_version") != 1 or m.get("status") != "complete":
        raise ValueError("invalid result manifest")
    if reference and (
        sha256(root / "result-manifest.json") != reference["result_manifest_sha256"]
        or m["request_fingerprint"] != reference["request_fingerprint"]
    ):
        raise ValueError("result identity mismatch")
    config = read_json(root / "config.json")
    expected_names = {*PRIMARY, config["model_name"] + ".onnx"}
    if set(m["hashes"]) != expected_names:
        raise ValueError("result artifact allowlist mismatch")
    if reference and m["execution_fingerprint"] != reference["execution_fingerprint"]:
        raise ValueError("execution identity mismatch")
    hashes = dict(m["hashes"])
    local = root / "local-render.json"
    if local.exists():
        renderer = read_json(local)
        if renderer["source_manifest_sha256"] != sha256(root / "result-manifest.json"):
            raise ValueError("local rendering source changed")
        for name in ("report.html", "report_ru.html"):
            hashes[name] = renderer["hashes"][name]
    verify_hashes(root, hashes, allow_missing_report=allow_missing_reports)
    metrics = read_json(root / "metrics.json")
    snapshot = root / "data-snapshot.json"
    config = read_json(root / "config.json")
    if metrics["model_sha256"] != hashes[config["model_name"] + ".onnx"] or metrics[
        "dataset_snapshot_sha256"
    ] != sha256(snapshot):
        raise ValueError("model/measurement identity mismatch")
    return m
