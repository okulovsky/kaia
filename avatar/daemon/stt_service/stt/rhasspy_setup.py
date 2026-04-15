from typing import Iterable
from brainbox import BrainBox
from .recognition_setup import IRecognitionSetup, RecognitionContext, STTConfirmation, IPostprocessor
from dataclasses import dataclass
from ..rhasspy_training import RhasspyHandler, IntentsPack
from brainbox.deciders import RhasspyKaldi, Collector


class RhasspyPostprocessor(IPostprocessor):
    def __init__(self, handler: RhasspyHandler):
        self.handler = handler

    def postprocess(self, result):
        try:
            return STTConfirmation(self.handler.parse_kaldi_output(result), result)
        except Exception as error:
            return STTConfirmation(None, result, error)

@dataclass
class RhasspyRecognitionSetup(IRecognitionSetup):
    model: str

    def create_task_and_postprocessor(self, context: RecognitionContext) -> tuple[BrainBox.Task, IPostprocessor]:
        task = (
            RhasspyKaldi
            .new_task(id=context.command.file.split('.')[0] + '.rhasspy')
            .transcribe(file=context.command.file, model=self.model)
        )
        handler = context.rhasspy_handlers[self.model]
        postprocessor = RhasspyPostprocessor(
            handler
        )
        return task, postprocessor

    @staticmethod
    def create_training_task(intents_packs: Iterable[IntentsPack]):
        builder = Collector.TaskBuilder()
        for pack in intents_packs:
            handler = RhasspyHandler(pack.templates)
            builder.append(
                RhasspyKaldi.new_task().train(pack.name, pack.language, handler.ini_file, pack.custom_words),
            )
        return builder.to_collector_pack('to_array')
