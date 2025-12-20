from typing import Iterable
from brainbox import BrainBox, IPostprocessor
from .recognition_setup import IRecognitionSetup, RecognitionContext, STTConfirmation
from dataclasses import dataclass
from ..rhasspy_training import RhasspyHandler, IntentsPack
from brainbox.deciders import RhasspyKaldi, Empty


class RhasspyPostprocessor(IPostprocessor):
    def __init__(self, handler: RhasspyHandler):
        self.handler = handler

    def postprocess(self, result, api):
        try:
            return STTConfirmation(self.handler.parse_kaldi_output(result), result)
        except Exception as error:
            return STTConfirmation(None, result, error)

@dataclass
class RhasspyRecognitionSetup(IRecognitionSetup):
    model: str

    def create_task(self, context: RecognitionContext) -> BrainBox.ITask:
        task = (BrainBox.Task
                .call(RhasspyKaldi)
                .transcribe(file=context.command.file, model=self.model)
                .to_task(id=context.command.file.split('.')[0] + '.rhasspy')
                )
        handler = context.rhasspy_handlers[self.model]
        postprocessor = RhasspyPostprocessor(
            handler
        )
        return BrainBox.ExtendedTask(
            task,
            postprocessor=postprocessor
        )

    @staticmethod
    def create_training_task(intents_packs: Iterable[IntentsPack]):
        tasks = []
        for pack in intents_packs:
            handler = RhasspyHandler(pack.templates)
            tasks.append(
                BrainBox.Task.call(RhasspyKaldi).train(pack.name, pack.language, handler.ini_file, pack.custom_words)
            )
        return BrainBox.CombinedTask(
            BrainBox.Task.call(Empty)(),
            tuple(tasks)
        )