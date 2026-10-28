from dataclasses import dataclass, field
from brainbox.deciders.text.llama_lora_sft_trainer.api import TrainingRun


@dataclass
class GenerationResult:
    input: str
    expected_output: str
    output: str

    def is_correct(self) -> bool:
        # The server returns the completion with the line breaks around it
        return self.output.strip() == self.expected_output.strip()


@dataclass
class CheckpointValStats:
    number: int
    generation_results: list[GenerationResult]

    def get_accuracy(self):
        correct = sum(result.is_correct() for result in self.generation_results)
        return correct / len(self.generation_results) if self.generation_results else 0.0

    def get_wrong_predictions(self):
        return [result for result in self.generation_results if not result.is_correct()]


@dataclass
class TrainStats:
    step: int
    grad_norm: float
    learning_rate: float
    loss: float

    @staticmethod
    def from_trainer_state(trainer_state: dict) -> list['TrainStats']:
        return [
            TrainStats(step=s["step"], grad_norm=s["grad_norm"], learning_rate=s["learning_rate"], loss=s["loss"])
            for s in trainer_state["log_history"]
            if "loss" in s
        ]


@dataclass
class TrainingRunStats:
    training_run: TrainingRun
    checkpoints_val_stats: list[CheckpointValStats]
    train_stats: list[TrainStats] = field(default_factory=list)

    def get_best_checkpoint(self) -> CheckpointValStats:
        # The latest of the equally good ones
        return max(self.checkpoints_val_stats, key=lambda c: (c.get_accuracy(), c.number))
