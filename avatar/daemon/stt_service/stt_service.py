import traceback
from typing import Callable
from grammatron import TemplateBase
from .stt import IRecognitionSetup, RecognitionContext, RhasspyRecognitionSetup, WhisperRecognitionSetup
from .rhasspy_training import RhasspyHandler
from .recognition_requests import STTTrainingCommand, IRecognitionRequest, TemplatesRecognitionRequest, FreeSpeechRecognitionRequest, RecognitionEvent
from ..common import message_handler, AvatarService, State, SoundEvent
from ..brainbox_service import BrainBoxService


def _default_templates_setup(context: str) -> IRecognitionSetup:
    return RhasspyRecognitionSetup(context)


def _default_free_speech_setup(language: str|None, prompt: str|None, template: TemplateBase|None) -> IRecognitionSetup:
    return WhisperRecognitionSetup(prompt, language, template)


class STTService(AvatarService):
    TrainingCommand = STTTrainingCommand

    def __init__(self,
                 state: State,
                 templates_setup: Callable[[str], IRecognitionSetup]|None = None,
                 free_speech_setup: Callable[[str|None, str|None, TemplateBase|None], IRecognitionSetup]|None = None,
                 default_request: IRecognitionRequest|None = None,
                 ):
        self.state = state
        self.templates_setup = templates_setup if templates_setup is not None else _default_templates_setup
        self.free_speech_setup = free_speech_setup if free_speech_setup is not None else _default_free_speech_setup
        self.default_request = default_request if default_request is not None else TemplatesRecognitionRequest()
        self.requested: IRecognitionRequest|None = None
        self.handlers: dict[str, RhasspyHandler] = {}

    def requires_brainbox(self):
        return True

    @message_handler
    def request(self, message: IRecognitionRequest) -> None:
        self.requested = message

    def resolve(self, request: IRecognitionRequest) -> IRecognitionSetup:
        if isinstance(request, TemplatesRecognitionRequest):
            return self.templates_setup(request.context)
        if isinstance(request, FreeSpeechRecognitionRequest):
            return self.free_speech_setup(request.language, request.prompt, request.template)
        raise TypeError(f"Unknown recognition request {request}")

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def recognize(self, event: SoundEvent) -> RecognitionEvent:
        request = self.default_request
        if self.requested is not None:
            request = self.requested
            self.requested = None
        try:
            setup = self.resolve(request)
            context = RecognitionContext(event.file_id, self.state.language, self.handlers)
            recognition_task, postprocessor = setup.create_task_and_postprocessor(context)
            bb_command = BrainBoxService.Command(recognition_task).as_reply_to(event)
            bb_result = self.client.run_synchronously(bb_command, BrainBoxService.Confirmation)
            if bb_result.result is None:
                return RecognitionEvent(event.file_id, None, bb_result.error)
            result = postprocessor.postprocess(bb_result.result)
        except Exception:
            return RecognitionEvent(event.file_id, None, traceback.format_exc())
        return RecognitionEvent(event.file_id, result.recognition, result.error)


    @message_handler
    def train(self, message: STTTrainingCommand) -> BrainBoxService.Command:
        for pack in message.packs:
            self.handlers[pack.context] = RhasspyHandler(pack.templates)
        task = RhasspyRecognitionSetup.create_training_task(message.packs)
        return (
            BrainBoxService
            .Command(task)
            .as_propagation_confirmation_to(message)
        )
