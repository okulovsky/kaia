import shutil
from typing import Iterable

from foundation_kaia.brainbox_utils import BrainboxReportItem
from foundation_kaia.marshalling import FileLike, FileLikeHandler, JSON
from interface import OneTrainerInterface, OneTrainerParameters, CheckpointInfo
from training import Training, Loc


class OneTrainerService(OneTrainerInterface):
    def train(
        self,
        training_id: str,
        parameters: OneTrainerParameters,
        dataset: FileLike,
        config: JSON = 'SDXL',
    ) -> Iterable[BrainboxReportItem[list[CheckpointInfo]]]:
        root = Loc.training_root(training_id)
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True)

        with open(root / 'dataset.zip', 'wb') as f:
            for chunk in FileLikeHandler.to_bytes_iterable(dataset):
                f.write(chunk)

        process = Training(training_id, parameters, config)
        return process.start_process(str(root / 'log.html'))

    def get_checkpoint(self, checkpoint: CheckpointInfo) -> FileLike:
        base = Loc.save_dir(checkpoint.training_id) if not checkpoint.is_final else Loc.output_dir(checkpoint.training_id)
        return base / checkpoint.filename

    def delete(self, training_id: str) -> None:
        shutil.rmtree(Loc.training_root(training_id))
