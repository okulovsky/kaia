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
        return BrainBox.Task.call(Vosk).transcribe_to_array(filename, self.vosk_model_name)


    def __call__(self,
                 cache: StepCache,
                 inference: VoiceInference,
                 model: VoiceModel,
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
        for case, option in cache.recognition.read_cases_and_single_options():
            verification = self.verifier.verify(
                name_to_text[case],
                option
            )
            result.append(UpsamplingResult(
                verification,
                name_to_text[case],
                name_to_path[case],
            ))

        cache.write_result(result)



