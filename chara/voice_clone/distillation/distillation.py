from chara import Chara, CaseCollection, CaseRepetition, BatchingPipeline, logger
from chara.common.tools import Wav
from .settings import DistillationSettings
from .training.training_and_export import CheckpointCase
from ..common import VoiceTrain, VoiceModel
from .upsampling import Upsampling, Verifier
from .training import piper_training, evaluate
from pathlib import Path
from foundation_kaia.logging import HtmlReport

class DistillationPipeline:
    def __init__(self, settings: DistillationSettings):
        self.settings = settings

    def __call__(self, name: str, source_voice: Path):
        dataset_path = Chara.call(self._prepare_dataset)(source_voice)
        checkpoint_cases = Chara.call(piper_training)(
            dataset_path,
            name,
            self.settings.language_settings.piper_base_model,
            self.settings.training_settings
        )
        checkpoint_cases: CaseCollection[CheckpointCase] = Chara.call(evaluate)(checkpoint_cases)
        wavs = []
        for case in checkpoint_cases.successes:
            w = Wav.one(case.path_to_voiceover_file)
            w.metadata['epoch'] = case.checkpoint.epoch
            wavs.append(w)
        lst = Wav.all(wavs)

        report = HtmlReport(Chara.current.folder / 'report.html')
        with logger.with_callback(report):
            logger.info(lst.draw().tables(order_by='epoch').widget())
        return checkpoint_cases



    def _batcher(self, summaries: list[CaseRepetition.Summary[Upsampling.Case]]) -> list[Upsampling.Case]:
        candidates = summaries
        total_duration = sum(s.successes[0].verification.duration for s in summaries if len(s.successes) > 0)
        if total_duration > self.settings.required_samples_duration_in_seconds:
            return []
        candidates = [s for s in candidates if len(s.successes) == 0]
        candidates = [s for s in candidates if len(s.errors) < self.settings.max_upsampling_attempts]
        candidates = list(sorted(candidates, key = lambda c: len(c.errors)))
        return [c.case for c in candidates[:self.settings.upsampling_batch_size]]


    def _prepare_dataset(self, source_voice: Path):
        @Chara.phase
        def train_voice_cloner():
            case = VoiceTrain.Case(self.settings.train, source_voice)
            case = VoiceTrain.pipeline(CaseCollection([case])).raise_if_any_error().successes[0]
            return case.model

        model: VoiceModel = Chara.previous.result
        verifier = Verifier(
            self.settings.language_settings.language,
            self.settings.language_settings.verifier_prefix_max_skip,
            self.settings.language_settings.verifier_suffix_max_skip,
            self.settings.language_settings.verifier_max_allowed_distance,
            self.settings.language_settings.verifier_additional_transform
        )
        upsampling_pipe = Upsampling.Pipeline(
            verifier,
            self.settings.language_settings.upsampling_prefix,
            self.settings.language_settings.upsampling_suffix
        )
        batching_pipe = BatchingPipeline[Upsampling.Case](
            upsampling_pipe,
            self._batcher,
            self.settings.max_upsampling_iterations
        )
        upsampling_cases = CaseCollection([
            Upsampling.Case(self.settings.inference, model, text)
            for text in self.settings.language_settings.language.upsampling_dataset_reader()
        ])
        upsampling_cases = Chara.call(batching_pipe.__call__)(upsampling_cases)

        dataset_path = Chara.current.folder/'dataset.zip'
        Upsampling.export(
            upsampling_cases.successes,
            Chara.current.folder/'dataset.zip'
        )
        return dataset_path






