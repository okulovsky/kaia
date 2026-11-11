"""The upstream augmentation/embedding recipe, without classifier training."""

import random
from pathlib import Path

import numpy as np
import soundfile as sf


def compute(input_folder, output_folder, manifest, settings, resources):
    from openwakeword.data import augment_clips

    from .embedding import compute_features_from_generator

    random.seed(settings["seed"])
    np.random.seed(settings["seed"])
    import torch

    torch.manual_seed(settings["seed"])
    torch.set_num_threads(1)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    groups = {
        name: []
        for name in (
            "positive_train",
            "positive_test",
            "negative_train",
            "negative_test",
        )
    }
    for item in manifest["samples"]:
        path = (Path(input_folder) / item["file"]).resolve()
        if not path.is_relative_to(Path(input_folder).resolve()):
            raise ValueError("unsafe input manifest path")
        info = sf.info(path)
        if info.samplerate != 16000 or info.channels != 1 or info.frames <= 0:
            raise ValueError(f"invalid normalized audio: {item['sample_id']}")
        groups[item["class_label"] + "_" + item["split"]].append(path)
    if any(not paths for paths in groups.values()):
        raise ValueError("all four audio groups must be nonempty")
    positive_test = groups["positive_test"]
    durations = [
        sf.info(positive_test[np.random.randint(0, len(positive_test))]).frames
        for _ in range(50)
    ]
    total_length = int(round(float(np.median(durations)) / 1000) * 1000) + 12000
    if total_length < 32000 or abs(total_length - 32000) <= 4000:
        total_length = 32000
    files = {}
    for group, paths in groups.items():
        label, split = group.rsplit("_", 1)
        name = label + "_features_" + split + ".npy"
        # Match upstream n_total: augmentation rounds diversify the generator;
        # upstream still caps output rows at the original input count.
        clips = [str(p) for p in paths] * settings["augmentation_rounds"]
        generator = augment_clips(
            clips,
            total_length=total_length,
            batch_size=min(settings["augmentation_batch_size"], len(paths)),
            background_clip_paths=resources["background_paths"],
            RIR_paths=resources["rir_paths"],
        )
        temporary = output_folder / (name + ".partial.npy")
        compute_features_from_generator(
            generator,
            n_total=len(paths),
            clip_duration=total_length,
            output_file=str(temporary),
            device="cpu",
            ncpu=1,
            model_paths=resources["model_paths"],
        )
        array = np.load(temporary, mmap_mode="r", allow_pickle=False)
        if array.ndim != 3 or array.shape[1:] != (16, 96) or not len(array):
            raise ValueError(
                f"feature shape is incompatible with (N,16,96): {array.shape}"
            )
        for start in range(0, len(array), 1024):
            if not np.isfinite(array[start : start + 1024]).all():
                raise ValueError("nonfinite features")
        del array
        final = output_folder / name
        temporary.replace(final)
        files[name] = final
    return files
