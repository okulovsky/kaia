import uuid
from datetime import datetime
from pathlib import Path
from grammatron import Template
from loguru import logger
from avatar.daemon import (
    ChatCommand, ChatService, InitializationEvent, TextEvent, NLUTextEvent, STTTrainingCommand, IntentsPack,
    TemplatesRecognitionRequest, MAIN_CONTEXT, StreamingSTTService,
)
from avatar.daemon.common import AvatarService, message_handler, TickEvent
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
        if message.file_id is not None or not _is_typed(message):
            return None
        return NLUTextEvent(f'{TYPED_PREFIX}{uuid.uuid4()}', message.text, TemplatesRecognitionRequest())


class TestbedChatService(ChatService):
    """
    Shows every recognition in the chat and in the log: the text that was heard, then the report of NLU.
    NLU sends the report at the same time as the recognition, so the report of a recording and its TextEvent
    come in either order: the first one waits for the second, and is shown alone if the second does not come.
    With `cache_folder`, the report of a recording also shows what Nemotron heard in each language.
    """
    WAIT_IN_SECONDS = 5

    def __init__(self, cache_folder: Path | None = None):
        super().__init__(None)
        self.cache_folder = cache_folder
        self.held_reports: dict[str, tuple[datetime, NLUReportEvent]] = {}
        self.held_texts: dict[str, tuple[datetime, TextEvent]] = {}

    @message_handler
    def on_report(self, message: NLUReportEvent) -> tuple[ChatCommand, ...]:
        logger.info(f'NLU report for {message.file_id}\n{message.to_str()}')
        # A typed text is already in the chat, and an empty or failed recognition gets no TextEvent
        if message.file_id.startswith(TYPED_PREFIX) or message.error is not None:
            return (self._report(message),)
        if message.text is None or message.text.strip() == '':
            return (self._report(message),)
        recording = _recording(message.file_id)
        if recording in self.held_texts:
            del self.held_texts[recording]
            return self._show(message)
        self.held_reports[recording] = (datetime.now(), message)
        return ()

    @message_handler
    def on_event(self, message: TextEvent) -> tuple[ChatCommand, ...]:
        if message.file_id is None:
            return (super().on_event(message),) if _is_typed(message) else ()
        recording = _recording(message.file_id)
        if recording in self.held_reports:
            return self._show(self.held_reports.pop(recording)[1])
        self.held_texts[recording] = (datetime.now(), message)
        return ()

    @message_handler
    def on_tick(self, message: TickEvent) -> tuple[ChatCommand, ...]:
        commands = []
        for recording, (since, report) in list(self.held_reports.items()):
            if (message.time - since).total_seconds() > self.WAIT_IN_SECONDS:
                del self.held_reports[recording]
                commands.append(self._report(report))
        for recording, (since, text) in list(self.held_texts.items()):
            if (message.time - since).total_seconds() > self.WAIT_IN_SECONDS:
                del self.held_texts[recording]
                commands.append(super().on_event(text))
        return tuple(commands)

    def _show(self, report: NLUReportEvent) -> tuple[ChatCommand, ...]:
        # The text that was heard, not the template of the recognized command
        return ChatCommand(report.text, ChatCommand.MessageType.from_user), self._report(report)

    def _report(self, report: NLUReportEvent) -> ChatCommand:
        languages = self._languages(report)
        text = report.to_str() if languages is None else languages + '\n' + report.to_str()
        return ChatCommand(text, ChatCommand.MessageType.system)

    def _languages(self, report: NLUReportEvent) -> str | None:
        # The result of Nemotron is in the cache under the name of the recording
        if self.cache_folder is None:
            return None
        files = list(Path(self.cache_folder).glob(f'{_recording(report.file_id)}.*transcribe_stream_languages*.jsonl'))
        if len(files) == 0:
            return None
        streams = StreamingSTTService.read_finals_by_stream(max(files, key=lambda f: f.stat().st_mtime).read_bytes())
        return _languages_line(streams, report.text)


def _is_typed(message: TextEvent) -> bool:
    # The Send button of the page sends an empty field too
    return isinstance(message.text, str) and message.text.strip() != ''


def _recording(file_id: str) -> str:
    # Streaming STT reports the recording itself, while STTIntegrationService sends its text with the fixed copy
    return file_id.split('.')[0]


def _languages_line(streams: dict[str, tuple[str, float]], chosen: str | None) -> str:
    heard = sorted(((language, text, confidence) for language, (text, confidence) in streams.items() if text != ''), key=lambda s: -s[2])
    parts, marked = [], False
    for language, text, confidence in heard:
        is_chosen = not marked and text == chosen
        marked = marked or is_chosen
        parts.append(f'{language} {confidence:.3f} {text!r}' + (' (chosen)' if is_chosen else ''))
    parts.extend(f'{language} nothing' for language, (text, _) in streams.items() if text == '')
    return 'languages: ' + ' | '.join(parts)
