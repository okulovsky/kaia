"""Native CPU processing smoke. Uses already prepared ONNX models; no downloads."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from wakeword.generation.local.features import compute
from wakeword.generation.local.normalization import normalize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    models = {
        name: str((args.models / name).resolve())
        for name in ("embedding_model.onnx", "melspectrogram.onnx")
    }
    for path in models.values():
        if not Path(path).is_file():
            parser.error("Missing prepared ONNX model: " + path)
    with tempfile.TemporaryDirectory(prefix="wakeword host smoke ") as temporary:
        root = Path(temporary)
        sf.write(root / "source.wav", np.ones((800, 2), dtype=np.float32) * 0.1, 8000)
        normalize(root / "source.wav", root / "normalized.wav")
        info = sf.info(root / "normalized.wav")
        assert (info.samplerate, info.channels, info.frames) == (16000, 1, 1600)
        sf.write(
            root / "background.wav",
            np.random.default_rng(42).normal(0, 0.01, 160000),
            16000,
        )
        rir = np.zeros(256, dtype=np.float32)
        rir[0] = 1
        sf.write(root / "rir.wav", rir, 16000)
        samples = []
        for group in (
            "positive_train",
            "positive_test",
            "negative_train",
            "negative_test",
        ):
            label, split = group.rsplit("_", 1)
            for index in range(2):
                name = group + str(index) + ".wav"
                sf.write(root / name, np.sin(np.arange(8000) * 0.05) * 0.2, 16000)
                samples.append(
                    {
                        "file": name,
                        "sample_id": group + str(index),
                        "class_label": label,
                        "split": split,
                    }
                )
        files = compute(
            root,
            args.output,
            {"samples": samples},
            {"seed": 42, "augmentation_rounds": 1, "augmentation_batch_size": 2},
            {
                "background_paths": [str(root / "background.wav")],
                "rir_paths": [str(root / "rir.wav")],
                "model_paths": models,
            },
        )
        shapes = {name: list(np.load(path).shape) for name, path in files.items()}
        assert all(shape == [2, 16, 96] for shape in shapes.values())
        result = {
            "models": {
                n: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                for n, p in models.items()
            },
            "shapes": shapes,
            "platform": sys.platform,
            "python": sys.version,
            "fixture": "synthetic signals; not a generated training dataset",
        }
        (args.output / "native-validation.json").write_text(
            json.dumps(result, indent=2)
        )
        print("NATIVE_HOST_FEATURES_OK", shapes)


if __name__ == "__main__":
    main()
