from brainbox import BrainBox
from .recognition_setup import IRecognitionSetup, RecognitionContext
from dataclasses import dataclass
from grammatron import TemplateBase
from brainbox.deciders import Vosk
from .free_speech_recognition import FreeSpeechPostprocessor

@dataclass
class VoskRecognitionSetup(IRecognitionSetup):
    model: str|None
    free_speech_recognition_template: None | TemplateBase = None

    def create_task(self, context: RecognitionContext) -> BrainBox.ITask:
        task = (
            BrainBox.Task
            .call(Vosk)
            .transcribe_to_string(file=context.command.file, model_name=self.model)
            .to_task(id=context.command.file.split('.')[0] + '.vosk')
        )
        postprocessor = FreeSpeechPostprocessor(self.free_speech_recognition_template)
        return BrainBox.ExtendedTask(
            task,
            postprocessor = postprocessor
        )

