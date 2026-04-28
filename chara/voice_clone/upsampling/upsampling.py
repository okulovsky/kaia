import os

from chara.common import ICache, ListCache, logger
from chara.common.pipelines import ICasePipeline
from .dto import UpsamplingResult
from .step import StepCache
from pathlib import Path
from typing import Callable
from ..common import VoiceModel, VoiceInference, VoiceTrain
from dataclasses import dataclass
from chara.common.tools import Wav
import zipfile
from .upsampling_step import UpsamplingCase, CaseCache


class UpsamplingCache(ICache):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.training = VoiceTrain.Cache()
        self.steps = ListCache[StepCache, list[UpsamplingResult]](StepCache)

    def export(self, path: Path):
        if path.is_file():
            os.unlink(path)
        with zipfile.ZipFile(path, 'w') as zip:
            for item in self.steps.read_result():
                if not item.verification.allowed:
                    continue
                wav = Wav.one(item.path_to_file).to_editable()
                wav = wav[item.verification.slice[0]['start']:item.verification.slice[-1]['end']]
                name = item.path_to_file.name
                zip.writestr(f'voice/'+name, wav.to_bytes())
                zip.writestr('voice/'+name.replace('.wav', '.txt'), item.text.encode('utf-8'))


@dataclass
class UpsamplingSettings:
    max_steps: int = 10
    max_attempts: int = 3
    batch_size: int = 50
    total_audio_duration_in_seconds: float|None = None


@dataclass
class UpsamplingPipeline:
    source: Path
    train: VoiceTrain
    inference: VoiceInference
    strings: list[str]
    step: Callable[[StepCache, VoiceModel, VoiceInference, list[str]], None]
    upsampling_settings: UpsamplingSettings

    def __call__(self, cache: UpsamplingCache):
        @logger.phase(cache.training)
        def _():
            VoiceTrain.pipeline(
                cache.training,
                self.train,
                self.source
            )

        model = cache.training.read_result()
        if len(model) != 1:
            raise ValueError("Expected exactly one model")
        model = model[0]

        @logger.phase(cache.steps)
        def _():
            results = []
            for i in range(self.upsampling_settings.max_steps):
                selected = UpsamplingPipeline.select(self.strings, results, self.upsampling_settings.max_attempts)[:self.upsampling_settings.batch_size]
                if len(selected) == 0:
                    break

                @logger.phase(cache.steps[i])
                def __():
                    self.step(cache.steps[i], model, self.inference, selected)

                results.extend(cache.steps[i].read_result())
                total_duration = sum(e.verification.duration for e in results if e.verification.allowed)
                logger.info(f"Currently produced audio of length {total_duration}")
                if (self.upsampling_settings.total_audio_duration_in_seconds is not None
                    and total_duration > self.upsampling_settings.total_audio_duration_in_seconds):
                    break

            cache.steps.write_result(results)

        cache.finalize()

    @staticmethod
    def select(strings: list[str], results: list[UpsamplingResult], max_attempts: int = 3) -> list[str]:
        attempts = {s: 0 for s in strings}
        for r in results:
            if r.verification.allowed:
                del attempts[r.text]
            else:
                attempts[r.text] += 1


        return [k for k, v in sorted(attempts.items(), key=lambda i: i[1]) if v < max_attempts]


