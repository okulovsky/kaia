import os

from chara.common import *
from chara.common.tools import Wav
from pathlib import Path

from foundation_kaia.logging import HtmlReport
from ..upsampling import UpsamplingCache, StepPipeline, UpsamplingPipeline, Verifier
from ..training import TrainingCache, TrainingPipeline
from .settings import DistillationSettings


class DistillationCache(ICache[Wav.List]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.upsampling = UpsamplingCache()
        self.exported_dataset = FileCache(custom_file_name='dataset.zip')
        self.training = TrainingCache()
        self.html_report_cache = FileCache(custom_file_name='html_report.html')

    def pipeline(self, source: Path, settings: DistillationSettings):
        @logger.phase(self.upsampling)
        def _():
            step_pipeline = StepPipeline(
                settings.language_settings.language.vosk_name,
                Verifier(
                    settings.language_settings.language,
                    settings.language_settings.verifier_prefix_max_skip,
                    settings.language_settings.verifier_suffix_max_skip,
                    settings.language_settings.verifier_max_allowed_distance,
                    settings.language_settings.verifier_additional_transform,
                ),
                settings.language_settings.step_prefix,
                settings.language_settings.step_suffix
            )
            upsamling_pipeline = UpsamplingPipeline(
                source,
                settings.train,
                settings.inference,
                settings.language_settings.language.upsampling_dataset_reader(),
                step_pipeline,
                settings.upsampling_settings
            )
            upsamling_pipeline(self.upsampling)


        @logger.phase(self.exported_dataset)
        def _():
            os.makedirs(self.exported_dataset.working_folder, exist_ok=True)
            self.upsampling.export(self.exported_dataset.cache_file_path)

        @logger.phase(self.training)
        def _():
            pipeline = TrainingPipeline(
                str(source).replace('/', '___'),
                settings.language_settings.piper_base_model,
                settings.training_settings,
                settings.language_settings.voiceover_example
            )
            pipeline(self.training, self.exported_dataset.cache_file_path)

        @logger.phase(self.html_report_cache)
        def _():
            lst = self.training.read_result()
            os.makedirs(self.html_report_cache.working_folder, exist_ok=True)
            with HtmlReport(self.html_report_cache.cache_file_path):
                logger.info(lst.draw().tables(order_by='epoch').widget())
