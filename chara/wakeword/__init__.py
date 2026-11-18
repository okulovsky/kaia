"""Chara orchestration for wakeword generation and remote training."""


def __getattr__(name):
    if name in ("GenerationPipeline", "WakewordPipeline", "generate_dataset", "run"):
        from . import generation_pipeline

        return getattr(generation_pipeline, name)
    if name in ("TrainingPipeline", "train_dataset"):
        from . import training_pipeline

        return getattr(training_pipeline, name)
    if name == "GenerationSettings":
        from .generation.settings import GenerationSettings

        return GenerationSettings
    if name in ("TrainingSettings", "render_training_report"):
        if name == "TrainingSettings":
            from brainbox.deciders.voice_analysis.wakeword_training.runtime.settings import (
                TrainingSettings,
            )

            return TrainingSettings
        from brainbox.deciders.voice_analysis.wakeword_training.runtime.reporting import (
            render_training_report,
        )

        return render_training_report
    if name == "run_training":
        from .training.pipeline import run_training

        return run_training
    if name == "run_full":
        from .training.full_pipeline import run_full

        return run_full
    raise AttributeError(name)
