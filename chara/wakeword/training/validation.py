"""Final measurements belong to the exported ONNX, not checkpoint history."""

import os
from pathlib import Path
from uuid import uuid4

import numpy as np

from ..generation.io import sha256, write_json
from .batches import row_batches, window_batches
from .export import cpu_session
from .metrics import calculate_metrics, valid_scores


def parity_sample(arrays, snapshot, settings):
    pieces = []
    indices = {}
    for name in ("positive_features_test", "negative_features_test"):
        # All supervised validation inputs are checked in bounded export batches.
        count = min(len(arrays[name]), 256)
        selected = np.linspace(0, len(arrays[name]) - 1, count, dtype=int)
        indices[name] = selected.tolist()
        pieces.append(np.array(arrays[name][selected], dtype=np.float32))
    bg = snapshot["background"]
    selected = np.linspace(
        0, bg["total_valid_windows"] - 1, min(256, bg["total_valid_windows"]), dtype=int
    )
    sample = []
    global_index = 0
    offset = 0
    for length in bg["segment_lengths"]:
        for index in selected[
            (selected >= global_index) & (selected < global_index + max(0, length - 15))
        ]:
            start = int(index - global_index)
            sample.append(
                np.array(
                    arrays["background_validation"][
                        offset + start : offset + start + 16
                    ],
                    dtype=np.float32,
                )
            )
        global_index += max(0, length - 15)
        offset += length
    indices["background_validation"] = selected.tolist()
    pieces.append(np.stack(sample))
    return np.concatenate(pieces), indices


def evaluate(model_path, arrays, snapshot, settings, root):
    root = Path(root)
    (root / "scores").mkdir(exist_ok=True)
    session = cpu_session(model_path, settings.num_threads)
    bg = snapshot["background"]
    records = {}
    loaded = {}
    sources = [
        (
            "positive_validation",
            len(arrays["positive_features_test"]),
            row_batches(
                arrays["positive_features_test"], settings.validation_batch_size
            ),
        ),
        (
            "negative_validation",
            len(arrays["negative_features_test"]),
            row_batches(
                arrays["negative_features_test"], settings.validation_batch_size
            ),
        ),
        (
            "background_validation",
            bg["total_valid_windows"],
            window_batches(
                arrays["background_validation"],
                bg["segment_lengths"],
                settings.validation_batch_size,
            ),
        ),
    ]
    for name, count, batches in sources:
        path = root / "scores" / (name + ".npy")
        temp = path.with_name(path.name + "." + uuid4().hex + ".tmp")
        output = np.lib.format.open_memmap(
            temp, mode="w+", dtype=np.float32, shape=(count,)
        )
        position = 0
        try:
            for batch in batches:
                scores = session.run(["output"], {"onnx::Flatten_0": batch})[0].reshape(
                    -1
                )
                valid_scores(scores)
                output[position : position + len(batch)] = scores
                position += len(batch)
            if position != count:
                raise ValueError("score count disagrees with snapshot")
            output.flush()
            output._mmap.close()
            os.replace(temp, path)
        finally:
            if not output._mmap.closed:
                output._mmap.close()
            temp.unlink(missing_ok=True)
        records[name] = {
            "path": str(path.relative_to(root)),
            "sha256": sha256(path),
            "shape": [count],
            "dtype": "float32",
            "order": "supervised-row"
            if name != "background_validation"
            else "segment-then-start-stride1",
        }
        loaded[name] = np.load(path, mmap_mode="r", allow_pickle=False)
    try:
        result = calculate_metrics(
            *(
                loaded[x]
                for x in (
                    "positive_validation",
                    "negative_validation",
                    "background_validation",
                )
            ),
            settings.threshold,
            bg["evaluated_frames"],
            bg["frame_step_seconds"],
        )
    finally:
        for value in loaded.values():
            value._mmap.close()
    result.update(
        model_sha256=sha256(model_path),
        dataset_snapshot_sha256=sha256(root / "data-snapshot.json"),
        inference_backend="ONNX Runtime CPU",
        scores_artifacts=records,
    )
    write_json(root / "metrics.json", result)
    return result
