from dataclasses import dataclass, field
from typing import Iterable

from foundation_kaia.brainbox_utils import BrainboxReportItem, brainbox_websocket, brainbox_endpoint
from foundation_kaia.marshalling import service, FileLike, JSON


@dataclass(frozen=True)
class CheckpointInfo:
    training_id: str
    filename: str
    step: int
    epoch: int
    is_final: bool


@dataclass
class OneTrainerParameters:
    name: str
    base_model: str
    batch_size: int = 4
    target_steps: int = 1500
    save_every_n_steps: int | None = None
    prompts: list[str] = field(default_factory=list)
    negatives: str | None = None


@service
class OneTrainerInterface:
    @brainbox_websocket
    def train(
        self,
        training_id: str,
        parameters: OneTrainerParameters,
        dataset: FileLike,
        config: JSON = "SDXL",
    ) -> Iterable[BrainboxReportItem[list[CheckpointInfo]]]:
        """Fine-tunes an SDXL LoRA from a zipped image dataset, streaming training progress."""
        ...

    @brainbox_endpoint
    def get_checkpoint(self, checkpoint: CheckpointInfo) -> FileLike:
        """Returns a checkpoint file (final or intermediate) given its CheckpointInfo."""
        ...

    @brainbox_endpoint
    def delete(self, training_id: str) -> None:
        """Deletes all data associated with a training session."""
        ...
