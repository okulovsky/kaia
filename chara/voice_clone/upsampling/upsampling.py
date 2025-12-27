from chara.common import ICache, ListCache, logger
from .dto import UpsamplingResult
from .step import StepCache
from pathlib import Path
from typing import Callable
from ..common import VoiceModel, VoiceInference, VoiceTrain
from dataclasses import dataclass

class UpsamplingCache(ICache[dict[str,Path]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.training = VoiceTrain.Cache()
        self.steps = ListCache[StepCache, list[UpsamplingResult]](StepCache)


@dataclass
class UpsamplingPipeline:
    source: Path
    train: VoiceTrain
    inference: VoiceInference
    strings: list[str]
    step: Callable[[StepCache, VoiceModel, VoiceInference, list[str]], None]
    max_steps: int = 10
    max_attempts: int = 3
    batch_size: int = 50

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

            for i in range(self.max_steps):
                selected = UpsamplingPipeline.select(self.strings, results, self.max_attempts)[:self.batch_size]
                if len(selected) == 0:
                    break

                @logger.phase(cache.steps[i])
                def __():
                    self.step(cache.steps[i], model, self.inference, selected)

                results.extend(cache.steps[i].read_result())

            cache.steps.write_result(results)

        results = cache.steps.read_result()
        accepted = {r.text: r.path_to_file for r in results if r.verification.allowed}
        cache.write_result(accepted)

    @staticmethod
    def select(strings: list[str], results: list[UpsamplingResult], max_attempts: int = 3) -> list[str]:
        attempts = {s: 0 for s in strings}
        for r in results:
            if r.verification.allowed:
                del attempts[r.text]
            else:
                attempts[r.text] += 1


        return [k for k, v in sorted(attempts.items(), key=lambda i: i[1]) if v < max_attempts]


