"""Full operation identity is separate from the existing generation result."""

from pathlib import Path

from ..generation.io import read_json, sha256, write_json
from .dto import FullRunResult
from .pipeline import run_training
from .state import fingerprint, run_lock


def run_full(generation_settings, training_settings, output, dataset=None):
    root = Path(output).resolve()
    try:
        with run_lock(root):
            marker = root / "full-run.json"
            identity = {
                "training_settings": training_settings.canonical(),
                "dataset": str(Path(dataset).resolve()) if dataset else None,
                "generation_settings": None
                if dataset
                else generation_settings.canonical(),
            }
            requested = fingerprint(identity)
            if marker.exists():
                previous = read_json(marker)
                if previous["request_fingerprint"] != requested:
                    raise ValueError(
                        "full run settings changed; choose a new output folder"
                    )
                if (
                    dataset is None
                    and (root / "generation/dataset/manifest.json").is_file()
                ):
                    generated_manifest = read_json(
                        root / "generation/dataset/manifest.json"
                    )
                    if (
                        generated_manifest.get("status") == "complete"
                        and generated_manifest["settings"]
                        == generation_settings.canonical()
                    ):
                        dataset = root / "generation"
            elif any(p.name != ".wakeword.lock" for p in root.iterdir()):
                raise ValueError(
                    "output is not an empty full run directory; choose a new output folder"
                )
            value = {
                "schema_version": 1,
                "status": "running",
                "request_fingerprint": requested,
                "request": identity,
            }
            write_json(marker, value)
            if dataset is None:
                from ..generation.pipeline import run

                try:
                    generated = run(generation_settings, root / "generation")
                    if generated.status != "complete":
                        raise RuntimeError("generation did not complete")
                except Exception as error:
                    value.update(
                        status="failed", error_stage="generation", error=str(error)
                    )
                    write_json(marker, value)
                    raise
                dataset = root / "generation"
            result = run_training(dataset, training_settings, root / "training")
            value.update(
                status=result.status,
                dataset=str(Path(dataset).resolve()),
                training_output=str(root / "training"),
                error_stage=result.error_stage,
                error=result.error,
            )
            if result.status == "complete":
                value["training_manifest_sha256"] = sha256(
                    root / "training/manifest.json"
                )
            write_json(marker, value)
            return FullRunResult(result.status, root, result, result.error)
    except Exception as error:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
        return FullRunResult("failed", root, error=str(error))
