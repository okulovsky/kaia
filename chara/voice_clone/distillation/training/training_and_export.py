from chara import Chara, brainbox_training_pipeline, ICase, BrainBoxCasePipeline, CaseCollection, logger
from brainbox.deciders import PiperTraining, Piper
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CheckpointCase(ICase):
    checkpoint: PiperTraining.Checkpoint
    local_path: Path | None = None
    text_to_voiceover: str|None = None
    path_to_voiceover_file: Path|None = None

def _case_to_export(case: CheckpointCase):
    return PiperTraining.new_task().export(case.checkpoint)

def piper_training(
    dataset: Path,
    name: str,
    base_model: str,
    parameters: PiperTraining.TrainingParameters,
) -> CaseCollection[CheckpointCase]:

    training_task = PiperTraining.new_task().train(name, base_model, parameters, dataset)
    checkpoint_data = Chara.call(brainbox_training_pipeline)(training_task)
    logger.info(f"Checkpoints available: {len(checkpoint_data)}")
    cases = CaseCollection([CheckpointCase(PiperTraining.Checkpoint(**c)) for c in checkpoint_data])

    pipe = BrainBoxCasePipeline(_case_to_export, 'local_path', result_to_file=True)
    cases = Chara.call(pipe.__call__, "DownloadingCheckpoints")(cases).raise_if_any_error()
    return cases