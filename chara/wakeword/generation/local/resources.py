"""Resource acquisition and preparation; manifests freeze resolved inputs."""

import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import requests

os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "120")
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")
from ..io import read_json, write_json
from ..run_state import run_lock

OPENWAKEWORD_REVISION = "368c03716d1e92591906a84949bc477f3a834455"


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def default_specs():
    base = "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/"
    hashes = {
        "embedding_model.onnx": "70d164290c1d095d1d4ee149bc5e00543250a7316b59f31d056cff7bd3075c1f",
        "melspectrogram.onnx": "ba2b0e0f8b7b875369a2c89cb13360ff53bac436f2895cced9f479fa65eb176f",
    }
    return [
        {
            "id": name,
            "kind": "model",
            "source": base + name,
            "revision": "v0.5.1",
            "sha256": hashes[name],
        }
        for name in ("embedding_model.onnx", "melspectrogram.onnx")
    ] + [
        {
            "id": "en_us_cmudict_forward.pt",
            "kind": "phonemizer",
            "revision": "524f09e81b3962ffa5b3ef5af9953bbc059cce99",
            "sha256": "c5db2e1b13575c822b13579482b2a623454f5d769b9257d28e91eedc9688bdeb",
            "source": "https://huggingface.co/NRC-CNRC/en_us_cmudict_ipa_forward_g2p/resolve/524f09e81b3962ffa5b3ef5af9953bbc059cce99/en_us_cmudict_forward.pt",
        },
        {
            "id": "mit_rir",
            "kind": "mit_rir",
            "source": "davidscripka/MIT_environmental_impulse_responses",
            "revision": "main",
        },
        {
            "id": "fma_small.zip",
            "kind": "background",
            "source": "https://os.unil.cloud.switch.ch/fma/fma_small.zip",
            "revision": "fma_small",
        },
        {
            "id": "acav.npy",
            "kind": "acav",
            "revision": "main",
            "source": "https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/openwakeword_features_ACAV100M_2000_hrs_16bit.npy",
        },
    ]


class ResourceInstaller:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def _download(self, spec, folder):
        target = folder / spec["id"]
        expected = spec.get("sha256")
        metadata = folder / "download.json"
        if target.exists():
            actual = digest(target)
            previous = json.loads(metadata.read_text()) if metadata.exists() else {}
            if actual != (expected or previous.get("sha256")):
                raise ValueError(f"damaged cached resource: {spec['id']}")
            return target, actual
        partial = target.with_name(target.name + ".partial")
        if spec["source"].startswith("file://"):
            from urllib.parse import urlparse
            from urllib.request import url2pathname

            local = Path(url2pathname(urlparse(spec["source"]).path)).resolve()
            if not local.is_file():
                raise ValueError("local resource file is missing")
            shutil.copyfile(local, partial)
            actual = digest(partial)
            if expected and actual != expected:
                raise ValueError(f"checksum mismatch: {spec['id']}")
            partial.replace(target)
            metadata.write_text(json.dumps({"sha256": actual}))
            return target, actual
        offset = partial.stat().st_size if partial.exists() else 0
        headers = {"Range": f"bytes={offset}-"} if offset else {}
        with requests.get(
            spec["source"], headers=headers, stream=True, timeout=(15, 120)
        ) as response:
            response.raise_for_status()
            if offset and response.status_code == 206:
                if not response.headers.get("Content-Range", "").startswith(
                    f"bytes {offset}-"
                ):
                    raise ValueError("invalid HTTP range")
                mode = "ab"
            else:
                mode = "wb"
            with partial.open(mode) as stream:
                for chunk in response.iter_content(1024 * 1024):
                    stream.write(chunk)
                stream.flush()
                os.fsync(stream.fileno())
        actual = digest(partial)
        if expected and actual != expected:
            raise ValueError(f"checksum mismatch: {spec['id']}")
        partial.replace(target)
        metadata.write_text(json.dumps({"sha256": actual}))
        return target, actual

    def _prepare(self, specs):
        import numpy as np
        import soundfile as sf

        self.root.mkdir(parents=True, exist_ok=True)
        specs = specs or default_specs()
        result = []
        for original in specs:
            spec = dict(original)
            if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", spec["id"]):
                raise ValueError("unsafe resource id")
            if spec.get("sha256") and not re.fullmatch("[0-9a-f]{64}", spec["sha256"]):
                raise ValueError("invalid resource checksum")
            # Freeze HF references before creating the cache identity.
            if spec["kind"] == "mit_rir" and spec["revision"] == "main":
                from huggingface_hub import HfApi

                spec["revision"] = HfApi().dataset_info(spec["source"]).sha
            if spec["kind"] == "acav" and "/resolve/main/" in spec["source"]:
                from huggingface_hub import HfApi

                spec["revision"] = (
                    HfApi().dataset_info("davidscripka/openwakeword_features").sha
                )
                spec["source"] = spec["source"].replace(
                    "/resolve/main/", f"/resolve/{spec['revision']}/"
                )
            key = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
            folder = self.root / key
            folder.mkdir(exist_ok=True)
            ready = folder / "prepared.json"
            if ready.exists():
                item = json.loads(ready.read_text())
                for artifact in item["artifacts"]:
                    path = self.root / artifact["file"]
                    if (
                        not path.resolve().is_relative_to(self.root)
                        or not path.is_file()
                        or digest(path) != artifact["sha256"]
                    ):
                        raise ValueError(f"damaged prepared resource: {spec['id']}")
                result.append(item)
                continue
            artifacts = []
            if spec["kind"] == "mit_rir":
                import datasets

                from .normalization import normalize

                dataset = datasets.load_dataset(
                    spec["source"], revision=spec["revision"], split="train"
                )
                raw = folder / "raw.wav"
                for index, row in enumerate(dataset):
                    sf.write(
                        raw,
                        np.asarray(row["audio"]["array"]),
                        row["audio"]["sampling_rate"],
                    )
                    target = folder / f"{index:04d}.wav"
                    normalize(raw, target)
                    artifacts.append(target)
                raw.unlink(missing_ok=True)
                source_hash = hashlib.sha256(
                    "".join(digest(path) for path in artifacts).encode()
                ).hexdigest()
            else:
                target, source_hash = self._download(spec, folder)
                kind = spec["kind"]
                if kind == "background":
                    from ..processing import extract_archive

                    source = folder / "extracted"
                    marker = folder / "extracted.complete"
                    if source.exists() and (
                        not marker.exists() or marker.read_text() != source_hash
                    ):
                        raise ValueError(
                            "incomplete FMA extraction: restore or clear this resource cache before retrying"
                        )
                    if not source.exists():
                        extract_archive(target, source)
                        marker.write_text(source_hash)
                    for index, path in enumerate(sorted(source.rglob("*.mp3"))[:1500]):
                        output = folder / f"{index:05d}.wav"
                        subprocess.run(
                            [
                                "ffmpeg",
                                "-y",
                                "-loglevel",
                                "error",
                                "-i",
                                str(path),
                                "-ac",
                                "1",
                                "-ar",
                                "16000",
                                str(output),
                            ],
                            check=True,
                        )
                        info = sf.info(output)
                        if info.frames <= 0 or info.samplerate != 16000:
                            raise ValueError("invalid FMA conversion")
                        artifacts.append(output)
                elif kind == "acav":
                    array = np.load(target, mmap_mode="r", allow_pickle=False)
                    n = len(array) // 10
                    m = len(array) // 100
                    if (
                        n <= 0
                        or m <= 0
                        or array.ndim != 3
                        or array.shape[-1] != 96
                        or array.shape[1] < 16
                        or array.dtype.kind not in "fiu"
                    ):
                        raise ValueError("invalid ACAV resource")
                    for name, start, count, flatten in [
                        ("acav_train.npy", 0, n, False),
                        ("acav_val.npy", n, m, True),
                    ]:
                        shape = (
                            (count * array.shape[1], 96)
                            if flatten
                            else (count, *array.shape[1:])
                        )
                        output = folder / name
                        mapped = np.lib.format.open_memmap(
                            output, mode="w+", dtype=array.dtype, shape=shape
                        )
                        for offset in range(0, count, 256):
                            batch = array[
                                start + offset : start + min(offset + 256, count)
                            ]
                            if not np.isfinite(batch).all():
                                raise ValueError("nonfinite ACAV features")
                            if flatten:
                                mapped[
                                    offset * array.shape[1] : (offset + len(batch))
                                    * array.shape[1]
                                ] = batch.reshape(-1, 96)
                            else:
                                mapped[offset : offset + len(batch)] = batch
                        mapped.flush()
                        del mapped
                        artifacts.append(output)
                    del array
                elif kind == "model":
                    import onnxruntime

                    onnxruntime.InferenceSession(
                        str(target), providers=["CPUExecutionProvider"]
                    )
                    artifacts.append(target)
                elif kind == "phonemizer":
                    from .phonemizer import prepare_checkpoint

                    prepared = prepare_checkpoint(target, folder / "compatible.pt")
                    artifacts.extend([prepared, target])
                elif kind in ("background_wav", "rir_wav"):
                    from .normalization import normalize

                    output = folder / "normalized.wav"
                    normalize(target, output)
                    artifacts.append(output)
                else:
                    raise ValueError(f"unsupported resource kind: {kind}")
            if not artifacts:
                raise ValueError(f"empty resource: {spec['id']}")
            if spec.get("sha256") and source_hash != spec["sha256"]:
                raise ValueError("resource checksum mismatch: " + spec["id"])
            item = dict(
                spec,
                sha256=source_hash,
                checksum_scope="artifact_manifest"
                if spec["kind"] == "mit_rir"
                else "download",
                artifacts=[
                    {
                        "file": str(path.relative_to(self.root)),
                        "sha256": digest(path),
                        "size": path.stat().st_size,
                    }
                    for path in artifacts
                ],
            )
            temporary = ready.with_suffix(".tmp")
            temporary.write_text(json.dumps(item, sort_keys=True))
            temporary.replace(ready)
            result.append(item)
        versions = {
            name: importlib.metadata.version(name)
            for name in (
                "numpy",
                "scipy",
                "soundfile",
                "onnxruntime",
                "torch",
                "torchaudio",
                "openwakeword",
                "audiomentations",
                "torch-audiomentations",
                "speechbrain",
                "pronouncing",
                "deep-phonemizer",
                "datasets",
                "huggingface-hub",
                "pyarrow",
            )
        }
        return {
            "resources": result,
            "versions": versions,
            "openwakeword_revision": OPENWAKEWORD_REVISION,
            "resource_root": str(self.root),
            "backend": "host-parler-v2",
        }

    def paths(self, manifest):
        if manifest.get("openwakeword_revision") != OPENWAKEWORD_REVISION:
            raise ValueError(
                "incompatible resource manifest: local recipe versions changed"
            )
        for package, version in manifest["versions"].items():
            if importlib.metadata.version(package) != version:
                raise ValueError(
                    f"incompatible local dependency: {package}; choose a new output folder"
                )
        output = {"background_paths": [], "rir_paths": [], "model_paths": {}}
        for resource in manifest["resources"]:
            files = []
            for artifact in resource["artifacts"]:
                path = (self.root / artifact["file"]).resolve()
                if not path.is_relative_to(self.root.resolve()) or not path.is_file():
                    raise ValueError(
                        "resource is unavailable in the local resource cache"
                    )
                files.append(str(path))
            kind = resource["kind"]
            if kind in ("background", "background_wav"):
                output["background_paths"].extend(files)
            elif kind in ("mit_rir", "rir_wav"):
                output["rir_paths"].extend(files)
            elif kind == "model":
                output["model_paths"][resource["id"]] = files[0]
            elif kind == "phonemizer":
                output["phonemizer_path"] = files[0]
        if not output["background_paths"] or not output["rir_paths"]:
            raise ValueError("background audio and RIR resources are required")
        return output

    def check_space(self, specs):
        specs = specs or default_specs()
        prepared = []
        if self.root.exists():
            for path in self.root.glob("*/prepared.json"):
                prepared.append(read_json(path))
        required = 0
        estimates = {
            "acav": 20 * 1024**3,
            "background": 17 * 1024**3,
            "mit_rir": 1024**3,
            "phonemizer": 200 * 1024**2,
        }
        for spec in specs:
            if spec["source"].startswith("file://"):
                continue
            if any(
                item.get("id") == spec["id"] and item.get("kind") == spec["kind"]
                for item in prepared
            ):
                continue
            required += estimates.get(spec["kind"], 10 * 1024**2)
        location = self.root
        while not location.exists():
            location = location.parent
        available = shutil.disk_usage(location).free
        if available < required:
            raise RuntimeError(
                f"Insufficient disk space for missing resources: approximately {required / 1024**3:.1f} GiB required, {available / 1024**3:.1f} GiB free at {location}. Set resource_folder in CONFIG to a larger drive."
            )

    def prepare(self, specs):
        self.check_space(specs)
        with run_lock(self.root):
            result = self._prepare(specs)
            write_json(self.root / "manifest.json", result)
            write_json(self.root / "requested.json", specs)
            return result

    def load(self, specs, verify=True):
        if not (self.root / "manifest.json").is_file():
            raise ValueError("local resources are not prepared; run make setup")
        if read_json(self.root / "requested.json") != specs:
            raise ValueError("resource configuration changed; run make setup")
        manifest = read_json(self.root / "manifest.json")
        for item in manifest["resources"]:
            for artifact in item["artifacts"]:
                path = (self.root / artifact["file"]).resolve()
                if not path.is_relative_to(self.root) or not path.is_file():
                    raise ValueError(
                        "missing or unsafe local resource; restore cache before retrying"
                    )
                if path.stat().st_size != artifact["size"] or (
                    verify and digest(path) != artifact["sha256"]
                ):
                    raise ValueError("damaged local resource: " + str(path))
        self.paths(manifest)
        return manifest
