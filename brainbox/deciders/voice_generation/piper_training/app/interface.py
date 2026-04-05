from foundation_kaia.marshalling_2 import service, FileLike
from foundation_kaia.brainbox_utils import BrainboxReportItem, brainbox_websocket, brainbox_endpoint
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

@dataclass
class CkptData:
    training_id: str
    version: str
    filename: str
    epoch: int
    steps: int



@dataclass
class PiperTrainingParameters:
    epochs: int = 5
    sample_rate: int = 22050
    batch_size: int = 8
    validation_split: float = 0.0
    checkpoint_epochs: int = 1
    precision: int = 32
    num_test_examples: int = 0
    keep_intermediate: bool = False
    single_speaker_to_multi_speaker: bool = False
    continue_existing: bool = False


@service
class PiperTrainingInterface:
    @brainbox_websocket
    def train(self, training_id: str, model: str, parameters: PiperTrainingParameters, dataset: Iterable[bytes]|FileLike) -> Iterable[BrainboxReportItem[list[CkptData]]]:
        ...


    @brainbox_endpoint
    def export(self, ckpt: CkptData) -> FileLike:
        ...

    @brainbox_endpoint
    def delete(self, training_id: str) -> None:
        ...
