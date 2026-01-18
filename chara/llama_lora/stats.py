from dataclasses import dataclass
from brainbox.deciders.text.llama_lora_sft_trainer.api import TrainingRun
import json


@dataclass
class GenerationResult:
    input: str
    expected_output: str
    output: str


@dataclass
class CheckpointValStats:
    number: int
    generation_results: list[GenerationResult]

    def get_accuracy(self):
        correct = sum(result.output == result.expected_output for result in self.generation_results)
        return correct / len(self.generation_results) if self.generation_results else 0.0

    def get_wrong_predictions(self):
        return [
            result for result in self.generation_results if result.output != result.expected_output
        ]


@dataclass
class TrainStats:
    step: int
    grad_norm: float
    learning_rate: float
    loss: float


@dataclass
class TrainingRunStats:
    training_run: TrainingRun
    checkpoints_val_stats: list[CheckpointValStats]
    train_stats: list[TrainStats]

    def __init__(self, training_run: TrainingRun, checkpoints_val_stats: list[CheckpointValStats]):
        self.training_run = training_run
        self.checkpoints_val_stats = checkpoints_val_stats
        self.train_stats = self.get_train_stats()

    def get_train_stats(self):
        hf_checkpoints = list((self.training_run.path / "hf_checkpoints").glob("checkpoint-*"))
        latest_hf_checkpoint = max(hf_checkpoints, key=lambda f: int(f.stem.split("-")[1]))
        with open(latest_hf_checkpoint / "trainer_state.json", "r") as f:
            trainer_state = json.load(f)
        train_stats = []
        for stats in trainer_state["log_history"]:
            train_stats.append(
                TrainStats(
                    step=stats["step"],
                    grad_norm=stats["grad_norm"],
                    learning_rate=stats["learning_rate"],
                    loss=stats["loss"],
                )
            )
        return train_stats
