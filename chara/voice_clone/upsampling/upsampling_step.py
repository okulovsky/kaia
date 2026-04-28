from dataclasses import dataclass
from ...common.pipelines import ICase, BrainBoxCasePipeline, CaseCache
from ...common import logger
from ..common import VoiceModel, VoiceInference
from .dto import VerifierResult
from pathlib import Path
from brainbox.deciders import Vosk
from typing import Any
from .verifier import Verifier


@dataclass
class UpsamplingCase(ICase):
    text: str
    file_path: Path|None = None
    file_id: str|None = None
    recognition: Any = None
    verification: VerifierResult|None = None


class UpsamplingCache(CaseCache[UpsamplingCase]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.voiceover = CaseCache[UpsamplingCase]()
        self.recognition = CaseCache[UpsamplingCase]()

class UpsamplingStepPipeline:
    def __init__(self,
                 inference: VoiceInference,
                 model: VoiceModel,
                 verifier: Verifier,
                 prefix: str = '',
                 suffix: str = '',
                 ):
        self.inference = inference
        self.voice_model = model
        self.verifier = verifier
        self.prefix = prefix
        self.suffix = suffix


    def _voiceover_task(self, case: UpsamplingCase):
        return self.inference.create_task(self.voice_model, self.prefix+case.text+self.suffix)

    def _voiceover_applicator(self, case: UpsamplingCase, option: Path):
        case.file_path = option
        case.file_id = option.name

    def _recognition_task(self, case: UpsamplingCase):
        return Vosk.new_task().transcribe_to_array(case.file_id, self.verifier.language.vosk_name)

    def _recognition_applicator(self, case: UpsamplingCase, option: Any):
        case.recognition = option

    def __call__(self, cache: CaseCache[UpsamplingCase], cases: list[UpsamplingCase]):
        inner = cache.create_subcache('inner', UpsamplingCache)
        @logger.phase(inner.voiceover)
        def _():
            pipe = BrainBoxCasePipeline(self._voiceover_task, self._voiceover_applicator, options_as_files=True)
            pipe(inner.voiceover, cases)

        cases = inner.voiceover.read_successful_cases()

        @logger.phase(inner.recognition)
        def _():
            pipe = BrainBoxCasePipeline(self._recognition_task, self._recognition_applicator)
            pipe(inner.recognition, cases)

        cases = inner.recognition.read_successful_cases()
        for case in cases:
            case.verification = self.verifier.verify(case.text, case.recognition)
            if not case.verification.allowed:
                case.error = "Verification failed for this case"

        inner.finalize()
        cache.write_result(cases)









