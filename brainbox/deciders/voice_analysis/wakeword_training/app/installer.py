"""Explicit installation of immutable shared training background."""

import json
import shutil
import urllib.request
from pathlib import Path

from foundation_kaia.brainbox_utils import Installer


class WakewordTrainingInstaller(Installer):
    def __init__(self, resources_folder="/resources"):
        super().__init__(resources_folder)

    def _core(self):
        try:
            from wakeword_core import io
        except ImportError:
            from brainbox.deciders.voice_analysis.wakeword_training.runtime import io
        return io

    def readiness(self):
        io = self._core()
        manifest = self.resources_folder / "background/manifest.json"
        try:
            profile = io.read_json(manifest)
            spec = self._read_spec()
            if (
                profile["profile_id"] != spec["profile_id"]
                or profile["feature_space"] != spec["feature_space"]
            ):
                raise ValueError("background profile does not match this image")
            if any(
                profile["resource"][key] != spec[key]
                for key in ("source", "revision", "sha256")
            ):
                raise ValueError("background source does not match this image")
            artifacts = profile["resource"]["artifacts"]
            if {item["file"] for item in artifacts} != {
                "acav_train.npy",
                "acav_val.npy",
            }:
                raise ValueError("invalid background artifact list")
            for artifact in artifacts:
                if io.sha256(manifest.parent / artifact["file"]) != artifact["sha256"]:
                    raise ValueError("background checksum mismatch")
            return {"protocol_version": 1, "ready": True, "profile": profile}
        except (OSError, ValueError, KeyError, TypeError) as error:
            return {"protocol_version": 1, "ready": False, "reason": str(error)}

    def install_service(self):
        # Repair is explicit. The generic marker alone cannot prove resources are intact.
        try:
            from wakeword_core.locking import run_lock
        except ImportError:
            from brainbox.deciders.voice_analysis.wakeword_training.runtime.locking import (
                run_lock,
            )
        with run_lock(self.resources_folder / "background"):
            self._execute_installation()
            if not self.readiness()["ready"]:
                raise RuntimeError("background installation did not pass verification")
            self.installation_file.touch()

    def _execute_installation(self):
        if self.readiness()["ready"]:
            return
        spec = json.loads(
            (Path(__file__).parent / "resource-profile.json").read_text(
                encoding="utf-8"
            )
        )
        base = self.resources_folder / "background"
        base.mkdir(parents=True, exist_ok=True)
        source = self._download_source(base, spec)
        artifacts = self._prepare_splits(base, source)
        self._publish_manifest(base, spec, artifacts)
        source.unlink()

    def _read_spec(self):
        path = Path(__file__).parent / "resource-profile.json"
        if not path.exists():
            path = Path(__file__).parents[1] / "files/resource-profile.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _download_source(self, base, spec):
        if shutil.disk_usage(base).free < 21 * 1024**3:
            raise RuntimeError(
                "At least 21 GiB free space required for ACAV installation"
            )
        source = base / "source.npy.partial"
        with (
            urllib.request.urlopen(spec["source"], timeout=120) as incoming,
            source.open("wb") as output,
        ):
            shutil.copyfileobj(incoming, output, 1024 * 1024)
        if self._core().sha256(source) != spec["sha256"]:
            raise ValueError("ACAV source checksum mismatch")
        return source

    def _prepare_splits(self, base, source):
        import numpy as np

        data = np.load(source, mmap_mode="r", allow_pickle=False)
        try:
            if data.ndim != 3 or data.shape[1] < 16 or data.shape[2] != 96:
                raise ValueError("invalid ACAV source")
            train_count, validation_count = len(data) // 10, len(data) // 100
            if not train_count or not validation_count:
                raise ValueError("empty ACAV split")
            return [
                self._write_split(base / "acav_train.npy", data, 0, train_count, False),
                self._write_split(
                    base / "acav_val.npy", data, train_count, validation_count, True
                ),
            ]
        finally:
            data._mmap.close()

    def _write_split(self, path, data, start, count, flatten):
        import numpy as np

        temporary = path.with_suffix(".partial")
        shape = (count * data.shape[1], 96) if flatten else (count, *data.shape[1:])
        result = np.lib.format.open_memmap(
            temporary, mode="w+", dtype=np.float32, shape=shape
        )
        try:
            for offset in range(0, count, 256):
                chunk = np.asarray(
                    data[start + offset : start + min(offset + 256, count)],
                    dtype=np.float32,
                )
                if not np.isfinite(chunk).all():
                    raise ValueError("non-finite ACAV source")
                if flatten:
                    result[
                        offset * data.shape[1] : (offset + len(chunk)) * data.shape[1]
                    ] = chunk.reshape(-1, 96)
                else:
                    result[offset : offset + len(chunk)] = chunk
            result.flush()
        finally:
            result._mmap.close()
        temporary.replace(path)
        return {
            "file": path.name,
            "sha256": self._core().sha256(path),
            "shape": list(shape),
            "dtype": "float32",
            "segment_length": int(data.shape[1]),
            "source_start": start,
            "source_count": count,
            "flattened": flatten,
        }

    def _publish_manifest(self, base, spec, artifacts):
        self._core().write_json(
            base / "manifest.json",
            {
                "profile_id": spec["profile_id"],
                "feature_space": spec["feature_space"],
                "resource": {
                    "id": "acav.npy",
                    "kind": "acav",
                    "source": spec["source"],
                    "revision": spec["revision"],
                    "sha256": spec["sha256"],
                    "artifacts": artifacts,
                },
            },
        )
