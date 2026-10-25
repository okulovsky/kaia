import uuid
from grammatron import Template
from loguru import logger
from avatar.daemon import (
    ChatCommand, ChatService, InitializationEvent, TextEvent, NLUTextEvent, STTTrainingCommand, IntentsPack,
    TemplatesRecognitionRequest, MAIN_CONTEXT,
)
from avatar.daemon.common import AvatarService, message_handler
from .reporting_nlu_service import NLUReportEvent

TYPED_PREFIX = 'typed-'


class TestbedService(AvatarService):
    """
    Replaces the Kaia driver in the testbed: gives the templates to NLUService and sends the typed texts
    to NLUService without the speech recognition.
    """
    def __init__(self, templates: list[Template]):
        self.templates = templates

    def requires_brainbox(self):
        return False

    @message_handler
    def on_initialization(self, message: InitializationEvent) -> STTTrainingCommand:
        return STTTrainingCommand([IntentsPack(MAIN_CONTEXT, tuple(self.templates))])

    @message_handler
    def on_typed_text(self, message: TextEvent) -> NLUTextEvent | None:
        # The recognized speech also comes as TextEvent, but with the file of the recording
        if message.file_id is not None or not isinstance(message.text, str):
            return None
        return NLUTextEvent(f'{TYPED_PREFIX}{uuid.uuid4()}', message.text, TemplatesRecognitionRequest())


class TestbedChatService(ChatService):
    """
    Shows the report of every recognition in the chat and in the log.
    The report of a recording comes from NLU before the TextEvent of this recording,
    so it is held back and shown right after the message with the recognized text.
    """
    def __init__(self):
        super().__init__(None)
        self.held_reports: dict[str, NLUReportEvent] = {}

    @message_handler
    def on_report(self, message: NLUReportEvent) -> ChatCommand | None:
        logger.info(f'NLU report for {message.file_id}\n{message.to_str()}')
        if message.file_id.startswith(TYPED_PREFIX) or message.error is not None:
            return _report_command(message)
        # An empty recognition gets no TextEvent, and there is nothing to show
        if message.text is not None and message.text.strip() != '':
            self.held_reports[message.file_id] = message
        return None

    @message_handler
    def on_event(self, message: TextEvent) -> tuple[ChatCommand, ...]:
        report = self.held_reports.pop(message.file_id, None) if message.file_id is not None else None
        if report is None:
            return (super().on_event(message),)
        # The text that was heard, not the template of the recognized command
        return ChatCommand(report.text, ChatCommand.MessageType.from_user), _report_command(report)


def _report_command(report: NLUReportEvent) -> ChatCommand:
    return ChatCommand(report.to_str(), ChatCommand.MessageType.system)
