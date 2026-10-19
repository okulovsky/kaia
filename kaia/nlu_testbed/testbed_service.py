import uuid
from grammatron import Template
from loguru import logger
from avatar.daemon import (
    ChatCommand, InitializationEvent, TextEvent, NLUTextEvent, STTTrainingCommand, IntentsPack,
    TemplatesRecognitionRequest, MAIN_CONTEXT,
)
from avatar.daemon.common import AvatarService, message_handler
from .reporting_nlu_service import NLUReportEvent

GREETING = 'Press "Talk" and say a command, or type it. Every phrase gets the report of the NLU.'


class TestbedService(AvatarService):
    """
    Replaces the Kaia driver in the testbed: gives the templates to NLUService, sends the typed texts
    to NLUService without the speech recognition, and shows the report of every recognition in the chat and in the log.
    """
    def __init__(self, templates: list[Template]):
        self.templates = templates

    def requires_brainbox(self):
        return False

    @message_handler
    def on_initialization(self, message: InitializationEvent) -> tuple[STTTrainingCommand | ChatCommand, ...]:
        return (
            STTTrainingCommand([IntentsPack(MAIN_CONTEXT, tuple(self.templates))]),
            ChatCommand(GREETING, ChatCommand.MessageType.system),
        )

    @message_handler
    def on_typed_text(self, message: TextEvent) -> NLUTextEvent | None:
        # The recognized speech also comes as TextEvent, but with the file of the recording
        if message.file_id is not None or not isinstance(message.text, str):
            return None
        return NLUTextEvent(f'typed-{uuid.uuid4()}', message.text, TemplatesRecognitionRequest())

    @message_handler
    def on_report(self, message: NLUReportEvent) -> ChatCommand:
        report = message.to_str()
        logger.info(f'NLU report for {message.file_id}\n{report}')
        return ChatCommand(report, ChatCommand.MessageType.system)
