from brainbox import BrainBox
from .recognition_setup import IRecognitionSetup, RecognitionContext, IPostprocessor
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

    def create_task_and_postprocessor(self, context: RecognitionContext) -> tuple[BrainBox.Task, IPostprocessor]:
        # The setup pins the language for good; the command carries the one from the current state.
        language = self.language if self.language is not None else context.command.language
        language_argument = None if language is None else dict(language=language)
        task = (
            Whisper
            .new_task(id=context.command.file.split('.')[0] + '.whisper')
            .transcribe_text(
                file=context.command.file,
                initial_prompt=self.prompt,
                model=self.model,
                options=language_argument
            )
        )
        postprocessor = FreeSpeechPostprocessor(self.free_speech_recognition_template)
        return task, postprocessor
