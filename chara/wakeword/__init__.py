"""Wakeword data generation and local training with lazy model imports."""

from .generation.settings import GenerationSettings

__all__ = [
    "GenerationSettings",
    "TrainingSettings",
    "WakewordPipeline",
    "render_training_report",
    "run",
    "run_full",
    "run_training",
]


def __getattr__(name):
    if name == "TrainingSettings":
        from .training.settings import TrainingSettings

        return TrainingSettings
    if name == "run_training":
        from .training.pipeline import run_training

        return run_training
    if name == "run_full":
        from .training.full_pipeline import run_full

        return run_full
    if name == "render_training_report":
        from .training.reporting import render_training_report

        return render_training_report
    if name in ("WakewordPipeline", "run"):
        from .generation.pipeline import WakewordPipeline, run

        return WakewordPipeline if name == "WakewordPipeline" else run
    raise AttributeError(name)
