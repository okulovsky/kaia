import os
import shutil
from pathlib import Path

from brainbox.framework import OnDemandDockerApi, FileLike, FileIO, RunConfiguration
from .controller import WhisperXController
from .settings import WhisperXSettings
from ...common import check_hf_model_access

class WhisperX(OnDemandDockerApi[WhisperXSettings, WhisperXController]):
    def __init__(self):
        pass

    def _get_dst_folder(self):
        return self.controller.resource_folder()

    def _make_output_dir(self, dirname: FileLike.Type):
        output_dir = Path(self._get_dst_folder() / dirname)
        os.makedirs(output_dir, exist_ok=True)

    def _move_file(self, filename: FileLike.Type):
        path = FileLike.get_path(FileLike(filename, self.cache_folder))
        target_dir = Path(self._get_dst_folder()) / 'files'
        shutil.rmtree(target_dir, ignore_errors=True)
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(path, target_dir)

    def execute(self, filename: FileLike.Type):
        self._move_file(filename)
        self._make_output_dir('output')

        if 'HF_TOKEN' not in os.environ:
            raise ValueError("""
To download the whisperx models, you need to create a Hugging Face token here https://huggingface.co/settings/tokens

Then, you need to place this token in HF_TOKEN environmental variable
            """)
        token=os.environ['HF_TOKEN']
        check_hf_model_access('pyannote/segmentation-3.0', token)
        check_hf_model_access('pyannote/speaker-diarization-3.1', token)

        configuration = RunConfiguration(
            detach_and_interactive=False,
            command_line_arguments=['--hf_token', token]
        )
        self.controller.run_with_configuration(configuration)

        return FileIO.read_text(self.controller.resource_folder() / self._get_dst_folder() / 'output' / 'output.json')


    Controller = WhisperXController
    Settings = WhisperXSettings
