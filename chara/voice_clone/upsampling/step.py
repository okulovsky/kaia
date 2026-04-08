from click.core import augment_usage_errors

from chara.common import ICache, logger, BrainBoxCache, Language, BrainBoxUnit
from ..common import VoiceInference, VoiceModel
from .dto import UpsamplingResult
from pathlib import Path
from .verifier import Verifier
from brainbox import  BrainBox
from brainbox.deciders import Vosk
from dataclasses import dataclass

class StepCache(ICache[list[UpsamplingResult]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.voiceover = VoiceInference.Cache()
        self.recognition = BrainBoxCache[str,list]()

@dataclass
class StepPipeline:
    vosk_model_name: str
    verifier: Verifier
    prefix: str = ''
    suffix: str = ''

    def _create_vosk_task(self, filename: str):
        return Vosk.new_task().transcribe_to_array(filename, self.vosk_model_name)


    def __call__(self,
                 cache: StepCache,
                 model: VoiceModel,
                 inference: VoiceInference,
                 strings: list[str],
                 ):
        augmented_string_to_string = {self.prefix+s+self.suffix:s for s in strings}

        @logger.phase(cache.voiceover, "Voiceover of given texts")
        def _():
            VoiceInference.pipeline(
                cache.voiceover,
                inference,
                model,
                augmented_string_to_string
            )

        name_to_path: dict[str, Path] = {}
        name_to_text: dict[str, str] = {}
        for w in cache.voiceover.read_result():
            name_to_path[w.path.name] = w.path
            name_to_text[w.path.name] = augmented_string_to_string[w.metadata['text']]

        @logger.phase(cache.recognition, "Recognition of texts")
        def _():
            unit = BrainBoxUnit(
                self._create_vosk_task,
            )
            unit.run(cache.recognition, name_to_path)


        result = []
        total_allowed_duration = 0
        for case, option in cache.recognition.read_cases_and_single_options():
            verification = self.verifier.verify(
                name_to_text[case],
                option
            )
            if verification.allowed:
                total_allowed_duration += verification.duration
            result.append(UpsamplingResult(
                verification,
                name_to_text[case],
                name_to_path[case],
            ))
        logger.info(f"Length of audio generated and checked at this step {total_allowed_duration}")
        cache.write_result(result)

    @staticmethod
    def for_language(language: Language):
        from .verifier import Verifier

        if language.name == 'en':
            verifier = Verifier(
                language,
                4,
                4,
                2,
            )

            return StepPipeline(
                language.vosk_name,
                verifier,
                "The beginning. ",
                " The end."
            )

        if language.name == 'de':
            verifier = Verifier(
                language,
                4,
                4,
                2,
                additional_transform=lambda z: z.replace('ß', 'ss')
            )

            return StepPipeline(
                language.vosk_name,
                verifier,
                "Der Beginn. ",
                " Das Ende."
            )

        raise ValueError(f"Preset is not available for language {Language.name}")


