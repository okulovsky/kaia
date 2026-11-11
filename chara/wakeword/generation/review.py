import re
import shutil
from pathlib import Path

from .io import write_json


def save_review(root, case):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", case.sample_id):
        raise ValueError("unsafe sample id")
    destination = Path(root) / "review" / case.sample_id
    if (
        destination.parent != (Path(root) / "review")
        or "/" in case.sample_id
        or "\\" in case.sample_id
    ):
        raise ValueError("unsafe sample id")
    destination.mkdir(parents=True, exist_ok=True)
    if case.source_audio is not None:
        source = Path(case.source_audio)
        if source.is_file() and not (destination / "audio.wav").exists():
            shutil.copyfile(source, destination / "audio.wav")
    write_json(
        destination / "record.json",
        {
            "sample_id": case.sample_id,
            "stage": case.error_stage,
            "reason_code": case.reason_code,
            "class_label": case.class_label,
            "split": case.split,
            "expected_text": case.text,
            "recognition": case.recognition,
            "recognized_text": " ".join(
                item.get("word", "")
                for item in (case.recognition or [])
                if isinstance(item, dict)
            ),
            "seed": case.seed,
            "voice_description": case.voice_description,
            "error": case.error,
            "source_audio": "audio.wav"
            if (destination / "audio.wav").is_file()
            else None,
        },
    )
    return destination
