"""Server-side dataset lifecycle; all paths belong to this server."""

import re
import shutil
from pathlib import Path

from .io import read_json, write_json
from .locking import run_lock
from .manifests import PARTS, identity, validate_dataset
from .portable_results import package_result
from .settings import TrainingSettings


class ServerTraining:
    def __init__(self, resources):
        self.resources = Path(resources)

    def folder(self, training_id):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", training_id):
            raise ValueError("unsafe training_id")
        return self.resources / "training" / training_id

    def describe(self, training_id):
        root = self.folder(training_id)
        path = root / "request.json"
        if not path.exists():
            return {"exists": False, "training_id": training_id}
        request = read_json(path)
        state_path = root / "artifacts/state.json"
        state = (
            read_json(state_path) if state_path.exists() else {"status": "receiving"}
        )
        return {
            "exists": True,
            "training_id": training_id,
            "request_fingerprint": request["fingerprint"],
            "status": state["status"],
            "training_complete": "training" in state.get("completed_stages", {}),
            "error_stage": state.get("error_stage"),
            "reference": read_json(root / "reference.json")
            if (root / "reference.json").exists()
            else None,
        }

    def train(self, training_id, parameters, expected, dataset):
        root = self.folder(training_id)
        with run_lock(root):
            manifest, profile = self._validate_inputs(dataset, expected)
            digest = self._bind_request(root, manifest, profile, parameters, expected)
            if (root / "reference.json").exists():
                return read_json(root / "reference.json")
            self._prepare_legacy_view(root, Path(dataset), manifest, profile)
            self._execute_training(root, parameters)
            reference = package_result(root / "artifacts", training_id, digest)
            write_json(root / "reference.json", reference)
            return reference

    def _validate_inputs(self, dataset, expected):
        manifest = validate_dataset(dataset, expected)
        profile = read_json(self.resources / "background/manifest.json")
        if (
            expected.get("resource_profile")
            and profile.get("profile_id") != expected["resource_profile"]
        ):
            raise ValueError("server resource profile mismatch")
        if profile["feature_space"] != manifest["feature_space"]:
            raise ValueError("incompatible background feature space")
        return manifest, profile

    def _bind_request(self, root, manifest, profile, parameters, expected):
        bound = {
            "corpus_id": manifest["corpus_id"],
            "settings": parameters,
            "expected": expected,
            "background": profile,
        }
        digest = identity(bound)
        path = root / "request.json"
        if path.exists() and read_json(path)["fingerprint"] != digest:
            raise ValueError("immutable training request changed; use new output")
        write_json(path, {"fingerprint": digest, "request": bound})
        return digest

    def _execute_training(self, root, parameters):
        from .execution import run_training

        result = run_training(
            root / "input",
            TrainingSettings(**parameters).validate(),
            root / "artifacts",
        )
        if result.status != "complete":
            raise RuntimeError(f"{result.error_stage}: {result.error}")

    def _prepare_legacy_view(self, root, source, manifest, profile):
        destination = root / "input/dataset"
        destination.mkdir(parents=True, exist_ok=True)
        artifacts = {}
        for name in PARTS:
            path = destination / (name + ".npy")
            if not path.exists():
                shutil.copyfile(source / (name + ".npy"), path)
            part = manifest["parts"][name]
            artifacts[name] = {
                "path": path.name,
                "sha256": part["sha256"],
                "shape": part["shape"],
            }
        resources = {
            "resource_root": str((self.resources / "background").resolve()),
            "resources": [profile["resource"]],
        }
        write_json(destination.parent / "resources.json", resources)
        settings = {
            "portable_corpus_id": manifest["corpus_id"],
            **manifest["preparation"],
            "name": manifest["target"]["name"],
            "target_variants": manifest["target"]["variants"],
        }
        write_json(
            destination / "manifest.json",
            {
                "status": "complete",
                "artifacts": artifacts,
                "settings": settings,
                "resources": resources,
                "lineage": manifest["lineage"],
            },
        )
