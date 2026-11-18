"""Stream and validate remote exports before local publication."""

import tempfile
from pathlib import Path

from brainbox.deciders.voice_analysis.wakeword_training.runtime.archives import (
    extract_archive,
)
from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import sha256
from brainbox.deciders.voice_analysis.wakeword_training.runtime.portable_results import (
    PRIMARY,
    verify_result,
)


def download(api, cache_name, root, reference, model_name):
    root = Path(root)
    archive = root / "result.zip"
    temporary = root / "result.zip.partial"
    size = 0
    with temporary.open("wb") as output:
        for chunk in api.cache.open(cache_name):
            size += len(chunk)
            if size > reference["archive_size"]:
                raise ValueError("result size mismatch")
            output.write(chunk)
    if (
        size != reference["archive_size"]
        or sha256(temporary) != reference["archive_sha256"]
    ):
        raise ValueError("result checksum mismatch")
    temporary.replace(archive)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        extracted = extract_archive(
            archive,
            Path(folder) / "result",
            {*PRIMARY, model_name + ".onnx", "result-manifest.json"},
        )
        verify_result(extracted, reference)
        for path in extracted.rglob("*"):
            if path.is_file():
                target = root / path.relative_to(extracted)
                target.parent.mkdir(parents=True, exist_ok=True)
                path.replace(target)
    verify_result(root, reference)
    return str(root / "result-manifest.json")
