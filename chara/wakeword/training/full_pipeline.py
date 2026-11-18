"""Deprecated full-cycle helper delegating to the two independent pipelines."""

from pathlib import Path

from .dto import FullRunResult
from .pipeline import run_training


def run_full(generation_settings, training_settings, output, dataset=None):
    from brainbox.deciders.voice_analysis.wakeword_training.runtime.io import write_json
    from chara.wakeword.generation_pipeline import generate_dataset

    root = Path(output).resolve()
    if dataset is None:
        generate_dataset(generation_settings, root / "generation")
        dataset = root / "generation"
    result = run_training(dataset, training_settings, root / "training")
    write_json(
        root / "full-run.json",
        {"status": result.status, "dataset": str(dataset), "error": result.error},
    )
    return FullRunResult(result.status, root, result, result.error)
