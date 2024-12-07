import os
import time
import zipfile
from pathlib import Path
from typing import Iterable
from unittest import TestCase

from kaia.brainbox.deciders.arch import LocalImageInstaller, DockerService, BrainBoxServiceRunner, DockerInstaller
from kaia.brainbox.core import IntegrationTestResult, BrainBoxTask, BrainBoxApi
from kaia.brainbox.deployment import SmallImageBuilder, LocalExecutor, LocalImageSource
from kaia.infra import FileIO, Loc

from .settings import KohyaSSSettings


class KohyaSSInstaller(DockerInstaller):
    def __init__(self, settings: KohyaSSSettings):
        self.settings = settings


        image_source = LocalImageSource('kohya_ss')

        image_builder = SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            None,
        )

        runner = BrainBoxServiceRunner(
            gpu_required=BrainBoxServiceRunner.GpuRequirement.Mandatory,
            publish_ports={self.settings.port: 7860},
            mount_resource_folders={
                'training': '/app/training'
            }
        )

        main_service = DockerService(
            self,
            None,
            None,
            runner,
        )

        super().__init__(image_source, main_service, image_builder)

        if self.settings.custom_models_folder is not None:
            self._models_folder = self.settings.custom_models_folder
        else:
            self._models_folder = self.resource_folder('models')

        runner.mount_custom_folders = {
            self._models_folder: '/app/models'
        }



        self.gradio_service = self.main_service.as_service_worker('--gradio')
        self.gradio_service._container_runner.publish_ports = {self.settings.port: 7860}
        self.gradio_service._container_runner.mount_custom_folders = {Loc.root_folder: '/repo'}



    def warmup(self, parameters: str|None):
        pass

    def cooldown(self, parameters: str|None):
        pass

    def create_brainbox_decider_api(self, parameters: str|None):
        from .api import KohyaSS
        return KohyaSS(self)

    def _brainbox_self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable[IntegrationTestResult]:
        yield IntegrationTestResult(0, None, "kohya_ss doesn't perform real computations in self-testing, only the integration test is performed.")

        from .api import KohyaSS, LoraTrainingSettings
        lora_settings = LoraTrainingSettings(
            'test_training',
            'Matroskin',
            'cat',
            mock_training=True
        )
        dataset_path = Path(__file__).parent/'dataset.zip'
        with zipfile.ZipFile(dataset_path, 'w') as zip_file:
            zip_file.writestr('image1.png','')
            zip_file.writestr('image1.txt',b'cat, fur, whiskers')
        id = api.add(BrainBoxTask.call(KohyaSS).run_lora_training(dataset_path, {}, lora_settings))
        seen_not_none_progress = False
        while True:
            job = api.get_job(id)
            if job.progress is not None:
                seen_not_none_progress = True
            time.sleep(0.5)
            if job.finished:
                break
        tc.assertTrue(seen_not_none_progress)
        result = api.join(id)
        tc.assertEquals(1, len(result['files']))
        result = api.download(result['files'][0])
        tc.assertEquals(
            b'koyha_ss_mock_output_file',
            FileIO.read_bytes(result)
        )







DOCKERFILE = f'''
FROM ghcr.io/bmaltais/kohya-ss-gui:latest

COPY kaia_main.py /app/kaia_main.py

ENTRYPOINT ["/usr/local/bin/python","/app/kaia_main.py"]
'''
