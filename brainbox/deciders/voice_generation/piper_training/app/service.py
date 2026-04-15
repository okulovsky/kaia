import os
import shutil
import tarfile
from foundation_kaia.logging import Logger, HtmlReport
from foundation_kaia.marshalling import FileLike, FileLikeHandler
from interface import PiperTrainingInterface, PiperTrainingParameters, CkptData
from training import Training, Loc
from installer import PiperTrainingInstaller
from foundation_kaia.brainbox_utils import subprocess_streaming_call, BrainboxReportItem
from typing import Iterable


class PiperTrainingService(PiperTrainingInterface):
    def __init__(self, installer: PiperTrainingInstaller):
        self.installer = installer

    def train(self,
              training_id: str,
              model: str,
              parameters: PiperTrainingParameters,
              dataset: Iterable[bytes]|FileLike) -> Iterable[BrainboxReportItem[list[CkptData]]]:
        path = Loc.get_training_folder(training_id)
        if not parameters.continue_existing:
            shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        with open(path/'dataset.zip', 'wb') as file:
            for bts in FileLikeHandler.to_bytes_iterable(dataset):
                file.write(bts)

        process = Training(training_id, model, parameters, self.installer)
        return process.start_process(str(path / 'log.html'))

    def delete(self, training_id: str) -> None:
        path = Loc.get_training_folder(training_id)
        shutil.rmtree(path)

    def export(self, ckpt: CkptData) -> FileLike:
        path = Loc.get_training_folder(ckpt.training_id)
        logger = Logger()
        log_path = path / f'export-{ckpt.filename}.html'

        with HtmlReport(log_path):
            source_path = Loc.get_checkpoint_path(ckpt)
            name, extension = source_path.name.split('.')
            export_dir = path / 'export'
            onnx_path = export_dir / (name + '.onnx')
            json_path = export_dir / (name + '.onnx.json')
            os.makedirs(export_dir, exist_ok=True)

            arguments = [
                'python3',
                '-m',
                'piper_train.export_onnx',
                str(source_path),
                str(onnx_path)
            ]
            for s in subprocess_streaming_call(arguments):
                logger.info(s)

            config_source = path / 'preprocessed' / 'config.json'
            shutil.copy(config_source, json_path)

            tar_path = export_dir / (name + '.tar')
            with tarfile.open(tar_path, 'w') as tar:
                tar.add(onnx_path, arcname=name + '.onnx')
                tar.add(json_path, arcname=name + '.onnx.json')

            return tar_path
