import os
from typing import Iterable
from unittest import TestCase

import requests

from ....framework import (
    RunConfiguration, TestReport, BrainboxImageBuilder, IImageBuilder, DockerWebServiceController,
    BrainBoxApi, BrainBoxTask, INotebookableController, File
)
from ...common import check_if_its_sound, download_file
from .settings import OpenVoiceSettings
from pathlib import Path
import zipfile


class OpenVoiceController(
    DockerWebServiceController[OpenVoiceSettings],
    INotebookableController,
):
    def get_image_builder(self) -> IImageBuilder|None:
        return BrainboxImageBuilder(
            Path(__file__).parent,
            '3.9.21',
            ('ffmpeg',),
            BrainboxImageBuilder.Repository(
                'https://github.com/myshell-ai/OpenVoice.git',
                'bb79fa78a5a7a7a3d7602b7f6d48705213a039c7',
            ),
            allow_arm64=True
        )

    def get_service_run_configuration(self, parameter: str|None) -> RunConfiguration:
        if parameter is not None:
            raise ValueError(f"`parameter` must be None for {self.get_name()}")
        return RunConfiguration(
            publish_ports={self.connection_settings.port:8080},
            mount_resource_folders={
                'pretrained/model/checkpoints' : '/home/app/checkpoints',
                'models' : '/models',
                'voices': '/voices',
                'temp': '/temp'
            },
        )

    def post_install(self):
        path = self.resource_folder('pretrained')/'checkpoints_1226.zip'
        download_file(
            'https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_1226.zip',
            path
        )
        if not zipfile.is_zipfile(path):
            raise zipfile.BadZipFile(f"The file {path} is not a valid zip file.")

        folder = self.resource_folder('pretrained','model')
        os.makedirs(folder, exist_ok=True)
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(folder)



    def get_notebook_configuration(self) -> RunConfiguration|None:
        return self.get_service_run_configuration(None).as_notebook_service()

    def get_default_settings(self):
        return OpenVoiceSettings()

    def create_api(self):
        from .api import OpenVoice
        return OpenVoice()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import OpenVoice

        reference_speaker = File.read(Path(__file__).parent / "lina.wav")
        api.execute(BrainBoxTask.call(OpenVoice).train('test_voice', [reference_speaker]))
        yield TestReport.last_call(api).href('training').with_comment("Training a model for a reference voice")

        source_speaker = File.read(Path(__file__).parent/"nikita.wav")
        task = BrainBoxTask.call(OpenVoice).generate(source_speaker, 'test_voice')
        result_file = api.execute(task)

        check_if_its_sound(api.open_file(result_file).content, tc)
        yield TestReport.last_call(api).href('href').result_is_file(File.Kind.Audio)


