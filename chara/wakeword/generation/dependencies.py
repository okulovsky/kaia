"""Local dependencies and tools for the pinned CPU data-preparation recipe."""

import shutil
import subprocess
import sys
from pathlib import Path

REQUIREMENTS = Path(__file__).resolve().parents[1] / "requirements-host.txt"
MODULES = (
    "numpy",
    "scipy",
    "soundfile",
    "onnxruntime",
    "torch",
    "torchaudio",
    "openwakeword.data",
    "audiomentations",
    "torch_audiomentations",
    "speechbrain",
    "pronouncing",
    "dp.phonemizer",
    "datasets",
)


def issues():
    import importlib

    result = []
    for name in MODULES:
        try:
            importlib.import_module(name)
        except Exception as error:  # noqa: BLE001 - Pipeline boundary records failures from remote services and native libraries.
            result.append(f"{name}: {error}")
    for line in (
        REQUIREMENTS.with_name("requirements-host.lock.txt").read_text().splitlines()
    ):
        if "==" in line and not line.startswith("#"):
            name, expected = line.split("==", 1)
            try:
                actual = importlib.metadata.version(name)
                if actual != expected:
                    result.append(f"{name}: {actual}, requires {expected}")
            except importlib.metadata.PackageNotFoundError:
                result.append(f"{name}: not installed")
    try:
        import json

        info = json.loads(
            importlib.metadata.distribution("openwakeword").read_text("direct_url.json")
            or "{}"
        )
        if (
            info.get("vcs_info", {}).get("commit_id")
            != "368c03716d1e92591906a84949bc477f3a834455"
        ):
            result.append("openwakeword: source revision mismatch; run make setup")
    except importlib.metadata.PackageNotFoundError:
        pass
    if not shutil.which("ffmpeg"):
        result.append(
            "ffmpeg: install FFmpeg and add it to PATH, then reopen the terminal"
        )
    return result


def install():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--prefer-binary",
            "-r",
            str(REQUIREMENTS.with_name("requirements-host.lock.txt")),
        ],
        check=True,
    )
    # New dependencies must be imported in a fresh process after pip changes.
    subprocess.run(
        [
            sys.executable,
            "-c",
            'from chara.wakeword.generation.dependencies import issues; import sys; errors=issues(); print("\\n".join(errors)); sys.exit(bool(errors))',
        ],
        cwd=REQUIREMENTS.parents[2],
        check=True,
    )
