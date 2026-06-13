import random
from chara import Chara, CaseCollection, CaseRepetition, BatchingPipeline, logger
from chara.common.tools import Wav, Drawer
from foundation_kaia.prompters import Referrer
from .settings import DistillationSettings
from .training.training_and_export import CheckpointCase
from ..common import VoiceTrain, VoiceModel
from .upsampling import Upsampling, Verifier
from .training import piper_training, evaluate
from pathlib import Path


class DistillationPipeline:
    def __init__(self, settings: DistillationSettings):
        self.settings = settings

    def __call__(self, name: str, source_voice: Path):
        trainer_case = Chara.call(self._train_voice_cloner)(source_voice)
        successes = Chara.call(self._prepare_dataset)(trainer_case.model)
        dataset_path = Chara.call(self._export_dataset)(successes)

        checkpoint_cases = Chara.call(piper_training)(
            dataset_path,
            name,
            self.settings.language_settings.piper_base_model,
            self.settings.training_settings
        )
        for case in checkpoint_cases.successes:
            case.text_to_voiceover = self.settings.language_settings.voiceover_example
        checkpoint_cases: CaseCollection[CheckpointCase] = Chara.call(evaluate)(checkpoint_cases)
        wavs = []
        for case in checkpoint_cases.successes:
            w = Wav.one(case.path_to_voiceover_file)
            w.metadata['epoch'] = case.checkpoint.epoch
            w.metadata['path'] = case.local_path
            wavs.append(w)

        with open(Chara.current.folder/'report.html', 'w') as report:
            report.write('<!DOCTYPE html>\n<html><body>')
            report.write('<h1>Source samples</h1>')
            report.write(
                Drawer(trainer_case.leveled_samples, Wav).tiles(5).to_html()
            )
            report.write("<h1>Intermediate samples</h1>")

            examples = []
            for i in range(50):
                case: Upsampling.Case = random.choice(successes)
                examples.append(case.voiceover_path)
            report.write(
                Drawer(examples, Wav).tiles(5).to_html()
            )

            report.write("<h1>Distilled samples</h1>")
            ref = Referrer[CheckpointCase]().ref
            report.write(
                Drawer(checkpoint_cases.successes, lambda z: Wav(z.path_to_voiceover_file))
                .table(ref.checkpoint.epoch, ref.local_path)
                .to_html()
            )

        return checkpoint_cases



    def _batcher(self, summaries: list[CaseRepetition.Summary[Upsampling.Case]]) -> list[Upsampling.Case]:
        candidates = summaries
        total_duration = sum(s.successes[0].verification.duration for s in summaries if len(s.successes) > 0)
        logger.info(f"Total duration for now: {total_duration}")
        logger.info(f"Successes: {sum(len(s.successes) for s in summaries)}")
        logger.info(f"Failures: {sum(len(s.errors) for s in summaries)}")
        if total_duration > self.settings.required_samples_duration_in_seconds:
            return []
        candidates = [s for s in candidates if len(s.successes) == 0]
        candidates = [s for s in candidates if len(s.errors) < self.settings.max_upsampling_attempts]
        candidates = list(sorted(candidates, key = lambda c: len(c.errors)))
        return [c.case for c in candidates[:self.settings.upsampling_batch_size]]

    def _train_voice_cloner(self, source_voice: Path):
        case = VoiceTrain.Case(self.settings.train, source_voice)
        case = VoiceTrain.pipeline(CaseCollection([case])).raise_if_any_error().successes[0]
        return case

    def _prepare_dataset(self, model: VoiceModel):
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
        successes = upsampling_cases.successes
        total_time = sum(c.verification.duration for c in successes)
        logger.info(f"Total samples: {len(successes)}")
        logger.info(f'Total time: {total_time} seconds')
        return successes

    def _export_dataset(self, successes: tuple[Upsampling.Case,...]):
        dataset_path = Chara.current.folder/'dataset.zip'
        Upsampling.export(
            successes,
            Chara.current.folder/'dataset.zip'
        )
        return dataset_path






