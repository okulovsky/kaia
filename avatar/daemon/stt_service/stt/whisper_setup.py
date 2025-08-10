from brainbox import BrainBox
from .recognition_setup import IRecognitionSetup, RecognitionContext
from dataclasses import dataclass
from grammatron import TemplateBase
from brainbox.deciders import Whisper
from .free_speech_recognition import FreeSpeechPostprocessor

@dataclass
class WhisperRecognitionSetup(IRecognitionSetup):
    prompt: str|None = None
    language: str|None = None
    free_speech_recognition_template: None | TemplateBase = None
    model: str = 'base'

    def create_task(self, context: RecognitionContext) -> BrainBox.ITask:
        language_argument = None
        language = context.command.language
        if language is not None:
            language_argument = dict(language=language)
        task = (
            BrainBox.Task
            .call(Whisper)
            .transcribe(
                file=context.command.file,
                initial_prompt=self.prompt,
                model=self.model,
                parameters=language_argument
            )
            .to_task(id=context.command.file.split('.')[0] + '.whisper')
        )
        postprocessor = FreeSpeechPostprocessor(self.free_speech_recognition_template)
        return BrainBox.ExtendedTask(
            task,
            postprocessor = postprocessor
        )
