from brainbox import BrainBox
from .recognition_setup import IRecognitionSetup, RecognitionContext, IPostprocessor
from dataclasses import dataclass
from grammatron import TemplateBase
from brainbox.deciders import Nemotron
from .free_speech_recognition import FreeSpeechPostprocessor


class NemotronPostprocessor(IPostprocessor):
    def __init__(self, template: TemplateBase | None):
        self.inner = FreeSpeechPostprocessor(template)

    def postprocess(self, result):
        confirmation = self.inner.postprocess(result['text'])
        confirmation.meta = result
        return confirmation


@dataclass
class NemotronRecognitionSetup(IRecognitionSetup):
    language: str | None = None
    free_speech_recognition_template: None | TemplateBase = None
    model: str = 'multilingual'

    def create_task_and_postprocessor(self, context: RecognitionContext) -> tuple[BrainBox.Task, IPostprocessor]:
        language = self.language if self.language is not None else context.command.language
        task = (
            Nemotron
            .new_task(id=context.command.file.split('.')[0] + '.nemotron')
            .transcribe(file=context.command.file, language=language or 'auto', model=self.model)
        )
        return task, NemotronPostprocessor(self.free_speech_recognition_template)
