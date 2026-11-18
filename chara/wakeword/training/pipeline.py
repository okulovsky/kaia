"""Deprecated entry point; training now runs in BrainBox."""

from chara.wakeword.training_pipeline import train_dataset


def run_training(dataset, settings, output, background_manifest=None):
    if background_manifest is not None:
        raise ValueError("Background is now managed by the remote training decider")
    from pathlib import Path

    from brainbox.deciders.voice_analysis.wakeword_training.runtime.dto import (
        TrainingResult,
    )
    from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import read_json
    from chara.wakeword.generation.packaging import package_dataset

    try:
        info = package_dataset(dataset)
        manifest = read_json(Path(info["dataset_folder"]) / "manifest.json")
        expected = {
            "target_variants": manifest["target"]["variants"],
            "minimum_positive_counts": {
                "train": manifest["parts"]["positive_features_train"][
                    "accepted_original_count"
                ],
                "validation": manifest["parts"]["positive_features_test"][
                    "accepted_original_count"
                ],
            },
        }
        return train_dataset(dataset, settings, expected, output)
    except Exception as error:  # noqa: BLE001 - Compatibility boundary preserves result diagnostics.
        return TrainingResult(
            "failed", Path(output), error_stage="remote_training", error=str(error)
        )
