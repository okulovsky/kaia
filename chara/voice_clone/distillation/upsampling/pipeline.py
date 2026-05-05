from dataclasses import dataclass
from chara.common import ICase, BrainBoxCasePipeline, CaseCollection, Language, Chara
from ...common import VoiceModel, VoiceInference
from .dto import VerifierResult
from pathlib import Path
from brainbox.deciders import Vosk
from typing import Any, Iterable
from .verifier import Verifier
import os
import zipfile
from chara.common.tools.sounds import Wav


@dataclass
class UpsamplingCase(ICase):
    inference: VoiceInference
    voice_model: VoiceModel
    text: str
    voiceover_path: Path|None = None
    recognition: Any = None
    verification: VerifierResult|None = None


class UpsamplingPipeline:
    def __init__(self,
                 verifier: Verifier,
                 prefix: str = '',
                 suffix: str = '',
                 ):
        self.verifier = verifier
        self.prefix = prefix
        self.suffix = suffix


    def _voiceover_task(self, case: UpsamplingCase):
        return case.inference.create_task(case.voice_model, self.prefix+case.text+self.suffix)

    def _recognition_task(self, case: UpsamplingCase):
        return Vosk.new_task().transcribe_to_array(case.voiceover_path.name, self.verifier.language.vosk_name)

    def _recognition_applicator(self, case: UpsamplingCase, option: Any):
        case.recognition = option

    def __call__(self, cases: CaseCollection[UpsamplingCase]) -> CaseCollection[UpsamplingCase]:
        voiceover_pipe = BrainBoxCasePipeline(self._voiceover_task, 'voiceover_path', result_to_file=True)
        cases = Chara.call(voiceover_pipe.__call__)(cases)
        recognition_pipe = BrainBoxCasePipeline(self._recognition_task, self._recognition_applicator)
        cases = Chara.call(recognition_pipe.__call__)(cases)

        for case in cases.successes:
            case.verification = self.verifier.verify(case.text, case.recognition)
            if not case.verification.allowed:
                case.error = "Verification failed"

        return CaseCollection(cases)





class Upsampling:
    Case = UpsamplingCase
    Pipeline = UpsamplingPipeline

    @staticmethod
    def export(cases: Iterable[UpsamplingCase], path: Path):
        if path.is_file():
            os.unlink(path)
            with zipfile.ZipFile(path, 'w') as zip:
                for case in cases:
                    if not case.verification.allowed:
                        continue
                    wav = Wav.one(case.voiceover_path).to_editable()
                    wav = wav[case.verification.slice[0]['start']:case.verification.slice[-1]['end']]
                    name = case.voiceover_path.name
                    zip.writestr(f'voice/' + name, wav.to_bytes())
                    zip.writestr('voice/' + name.replace('.wav', '.txt'), case.text.encode('utf-8'))

