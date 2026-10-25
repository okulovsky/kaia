import json
import traceback
from pathlib import Path
from brainbox.deciders import Nemotron
from ..common import message_handler, AvatarService, State, SoundStreamingStartEvent
from ..brainbox_service import BrainBoxService
from ..stt_service import IRecognitionRequest, TemplatesRecognitionRequest, FreeSpeechRecognitionRequest
from .nlu_text_event import NLUTextEvent


class StreamingSTTService(AvatarService):
    def __init__(self,
                 state: State,
                 cache_folder: Path,
                 default_request: IRecognitionRequest|None = None,
                 nemotron_model: str = 'multilingual',
                 languages: tuple[str, ...] | None = None,
                 ):
        """
        With `languages`, the templates are recognized in each of these languages at once, and the text of the most
        confident stream is chosen with `choose_text`. `auto` alone takes Russian for Ukrainian or Vietnamese,
        and a language outside of `languages` is never chosen. It takes `len(languages)` times the computation of `auto`.
        """
        self.state = state
        self.cache_folder = Path(cache_folder)
        self.default_request = default_request if default_request is not None else TemplatesRecognitionRequest()
        self.nemotron_model = nemotron_model
        self.languages = languages
        self.requested: IRecognitionRequest|None = None

    def requires_brainbox(self):
        return True

    @message_handler
    def request(self, message: IRecognitionRequest) -> None:
        self.requested = message

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def transcribe(self, event: SoundStreamingStartEvent) -> NLUTextEvent:
        request = self.default_request
        if self.requested is not None:
            request = self.requested
            self.requested = None
        language = 'auto'
        if isinstance(request, FreeSpeechRecognitionRequest):
            language = request.language or self.state.language or 'auto'
        builder = Nemotron.new_task(id=event.file_id.split('.')[0] + '.nemotron-stream')
        several_languages = language == 'auto' and self.languages is not None
        if several_languages:
            task = builder.transcribe_stream_languages(event.file_id, languages=list(self.languages), model=self.nemotron_model)
        else:
            task = builder.transcribe_stream(event.file_id, language=language, model=self.nemotron_model)
        try:
            result = self.client.run_synchronously(BrainBoxService.Command(task).as_reply_to(event), BrainBoxService.Confirmation)
            if result.result is None:
                raise ValueError(f"Expected result, error\n{result.error}")
            content = (self.cache_folder / result.result).read_bytes()
            if several_languages:
                text = self.choose_text(self.read_finals_by_stream(content), self.languages, self.state.language)
            else:
                text = self.read_final_text(content)
        except Exception:
            # A cancelled recording is deleted while it is read, and the job fails: the request is still pending
            if self.requested is None and request is not self.default_request:
                self.requested = request
            return NLUTextEvent(event.file_id, None, request, traceback.format_exc())
        return NLUTextEvent(event.file_id, text, request)

    @staticmethod
    def _read_events(content: bytes) -> list[dict]:
        return [json.loads(line) for line in content.decode('utf-8').splitlines() if line.strip() != '']

    @staticmethod
    def _join_finals(events: list[dict]) -> str:
        finals = [e for e in events if e.get('is_final')]
        if len(finals) == 0:
            finals = events[-1:]
        return ' '.join(e['text'].strip() for e in finals if e['text'].strip() != '')

    @staticmethod
    def read_final_text(content: bytes) -> str:
        return StreamingSTTService._join_finals(StreamingSTTService._read_events(content))

    @staticmethod
    def read_finals_by_stream(content: bytes) -> dict[str, tuple[str, float]]:
        """
        For each stream, the text and its confidence: the mean confidence of the final results with text,
        1 if the decider gives none
        """
        by_stream = {}
        for event in StreamingSTTService._read_events(content):
            by_stream.setdefault(event['stream'], []).append(event)
        result = {}
        for stream, events in by_stream.items():
            confidences = [
                e['confidence'] for e in events
                if e.get('is_final') and e['text'].strip() != '' and e.get('confidence') is not None
            ]
            confidence = sum(confidences) / len(confidences) if len(confidences) > 0 else 1.0
            result[stream] = (StreamingSTTService._join_finals(events), confidence)
        return result

    @staticmethod
    def choose_text(results: dict[str, tuple[str, float]], languages: tuple[str, ...], state_language: str | None = None) -> str:
        """
        Chooses the text of the most confident stream among the ones forced to `languages` that heard anything.
        A stream forced to a wrong language mostly gives nothing, or a transliteration that Nemotron is less confident in.
        Equal confidences (e.g. a decider that gives none) are decided by the state language, then by the order of `languages`.
        """
        candidates = [language for language in languages if results.get(language, ('', 0.0))[0] != '']
        if len(candidates) == 0:
            return ''

        def rank(language: str):
            in_state = state_language is not None and language.lower().startswith(state_language.lower())
            return results[language][1], in_state, -languages.index(language)

        return results[max(candidates, key=rank)][0]
