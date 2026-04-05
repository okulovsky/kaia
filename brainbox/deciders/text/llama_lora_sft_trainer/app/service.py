import json
import uuid
from pathlib import Path
from typing import Iterable

from foundation_kaia.brainbox_utils import LongBrainboxProcess, BrainboxReportItem, logger, subprocess_streaming_call
from foundation_kaia.marshalling_2 import FileLike, FileLikeHandler
from interface import LlamaLoraSFTTrainerInterface, TrainingRun, TrainingSettings

EXPERIMENTS_ROOT = Path("/resources/experiments")


class LlamaLoraSFTTrainerProcess(LongBrainboxProcess[TrainingRun]):
    def __init__(self, model_id: str, adapter_name: str, guid: str):
        self.model_id = model_id
        self.adapter_name = adapter_name
        self.guid = guid

    def execute(self) -> TrainingRun:
        for line in subprocess_streaming_call(
            ['python3', 'main/trainer.py', self.model_id, self.adapter_name, self.guid]
        ):
            logger.info(line)
        return TrainingRun(model_id=self.model_id, adapter_name=self.adapter_name, guid=self.guid)


class LlamaLoraSFTTrainerService(LlamaLoraSFTTrainerInterface):
    def train(
        self,
        model_id: str,
        adapter_name: str,
        settings: TrainingSettings,
        dataset: FileLike,
    ) -> Iterable[BrainboxReportItem[TrainingRun]]:
        guid = uuid.uuid4().hex
        exp_folder = EXPERIMENTS_ROOT / model_id / adapter_name / guid
        exp_folder.mkdir(parents=True, exist_ok=True)

        with open(exp_folder / "train.jsonl", "wb") as f:
            for chunk in FileLikeHandler.to_bytes_iterable(dataset):
                f.write(chunk)

        with open(exp_folder / "settings.json", "w") as f:
            json.dump(settings.__dict__, f)

        process = LlamaLoraSFTTrainerProcess(model_id, adapter_name, guid)
        return process.start_process(str(exp_folder / "log.html"))
