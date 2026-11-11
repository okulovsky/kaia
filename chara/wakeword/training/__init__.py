"""Local training. Importing configuration does not load a model."""

from .settings import TrainingSettings as TrainingSettings


def __getattr__(name):
    if name == "run_training":
        from .pipeline import run_training

        return run_training
    if name == "run_full":
        from .full_pipeline import run_full

        return run_full
    if name == "render_training_report":
        from .reporting import render_training_report

        return render_training_report
    raise AttributeError(name)
