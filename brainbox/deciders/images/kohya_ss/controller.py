import os
import shutil
from typing import Iterable
from unittest import TestCase
from ....framework import (
    SmallImageBuilder, IImageBuilder, BrainBoxApi, BrainBoxTask, OnDemandDockerController, Loc,
    RunConfiguration, TestReport
)
from .settings import KohyaSSSettings
from pathlib import Path
import zipfile
import time



class KohyaSSController(OnDemandDockerController[KohyaSSSettings]):
    def get_image_builder(self) -> IImageBuilder|None:
        return SmallImageBuilder(
            Path(__file__).parent/'container',
            DOCKERFILE,
            None
        )

    def get_base_configuration(self) -> RunConfiguration:
        return RunConfiguration(
            mount_resource_folders={
                'models' : '/app/models',
                'training': '/app/training'
            },
            detach_and_interactive=False
        )

    def run_gradio(self):
        cfg = self.get_base_configuration()
        cfg.command_line_arguments=['--gradio']
        cfg.publish_ports = {self.settings.port: 7860}
        self.run_with_configuration(cfg)

    def get_default_settings(self):
        return KohyaSSSettings()

    def create_api(self):
        from .api import KohyaSS
        return KohyaSS()

    def _self_test_internal(self, api: BrainBoxApi, tc: TestCase) -> Iterable:
        from .api import KohyaSS, LoraTrainingSettings

        yield TestReport.main_section_content(
            "KohyaSS doesn't run the real training in self-test. Self-test checks the input/output structure only"
        )

        lora_settings = LoraTrainingSettings(
            'test_training',
            'Matroskin',
            'cat',
            mock_training=True
        )
        dataset_path = Path(__file__).parent / 'dataset.zip'
        with zipfile.ZipFile(dataset_path, 'w') as zip_file:
            zip_file.writestr('image1.png', '')
            zip_file.writestr('image1.txt', b'cat, fur, whiskers')
        id = api.add(BrainBoxTask.call(KohyaSS).run_lora_training(dataset_path, {}, lora_settings))
        seen_not_none_progress = False
        while True:
            job = api.summary(ids=[id])[0]
            if job['progress'] is not None:
                seen_not_none_progress = True
            time.sleep(0.5)
            if job['finished']:
                break
        result = api.join(id)
        tc.assertTrue(seen_not_none_progress)
        tc.assertTrue((api.cache_folder/result['log_file']).is_file())

        export_folder = Loc.temp_folder/'kohya_ss_self_test'
        shutil.rmtree(export_folder, ignore_errors=True)
        postprocessor = KohyaSS.Exporter(export_folder, False, False)
        postprocessor.postprocess(result, api)

        files = os.listdir(export_folder)
        tc.assertSetEqual(
            {
                result['training_id'] + '.safetensors',
                result['training_id'] + '.safetensors.description.json',
                result['training_id'] + '-000000.safetensors',
                result['training_id'] + '-000000.safetensors.description.json',

            },
            set(files)
        )
        tc.assertFalse(Path(result['training_folder']).is_dir())

        yield TestReport.last_call(api)






DOCKERFILE = f'''
FROM ghcr.io/bmaltais/kohya-ss-gui:latest

COPY kaia_main.py /app/kaia_main.py

ENTRYPOINT ["/usr/local/bin/python","/app/kaia_main.py"]
'''
