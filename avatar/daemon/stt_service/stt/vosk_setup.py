from brainbox import BrainBox
from .recognition_setup import IRecognitionSetup, RecognitionContext, IPostprocessor
from dataclasses import dataclass
from grammatron import TemplateBase
from brainbox.deciders import Vosk
from .free_speech_recognition import FreeSpeechPostprocessor

@dataclass
class VoskRecognitionSetup(IRecognitionSetup):
    model: str|None
    free_speech_recognition_template: None | TemplateBase = None

    def create_task_and_postprocessor(self, context: RecognitionContext) -> tuple[BrainBox.Task, IPostprocessor]:
        task = (Vosk
                .new_task(id=context.command.file.split('.')[0] + '.vosk')
                .transcribe_to_string(file=context.command.file, model=self.model)
                )
        postprocessor = FreeSpeechPostprocessor(self.free_speech_recognition_template)
        return task, postprocessor

