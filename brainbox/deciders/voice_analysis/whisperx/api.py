import os
import shutil
from pathlib import Path

from brainbox.framework import OnDemandDockerApi, FileLike, FileIO, RunConfiguration
from .controller import WhisperXController
from .settings import WhisperXSettings

class WhisperX(OnDemandDockerApi[WhisperXSettings, WhisperXController]):
    def __init__(self):
        pass

    def _get_dst_folder(self):
        return self.controller.resource_folder()

    def _make_output_dir(self, dirname: FileLike.Type):
        output_dir = Path(self._get_dst_folder() / dirname)
        os.makedirs(output_dir, exist_ok=True)

    def _move_file(self, filename: FileLike.Type):
        source_dir = Path(__file__).parent / 'files'
        target_dir = Path(self._get_dst_folder()) / 'files'
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(source_dir / filename, target_dir)

    def execute(self, filename: FileLike.Type):
        self._move_file(filename)
        self._make_output_dir('output')

        configuration = RunConfiguration(
            detach_and_interactive=False
        )
        self.controller.run_with_configuration(configuration)

        return FileIO.read_text(self.controller.resource_folder() / self._get_dst_folder() / 'output' / 'output.json')


    Controller = WhisperXController
    Settings = WhisperXSettings
