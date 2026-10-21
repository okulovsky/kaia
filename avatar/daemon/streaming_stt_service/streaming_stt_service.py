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
        With `languages`, the templates are recognized in `auto` and in each of these languages at once,
        and one of the texts is chosen with `choose_text`: in noise, `auto` alone takes Russian for Vietnamese etc.
        It takes `len(languages) + 1` times the computation of `auto` alone.
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
            task = builder.transcribe_stream_languages(event.file_id, languages=['auto', *self.languages], model=self.nemotron_model)
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
    def read_finals_by_stream(content: bytes) -> dict[str, tuple[str, list[str]]]:
        """For each stream, the text and the languages Nemotron tagged it with"""
        by_stream = {}
        for event in StreamingSTTService._read_events(content):
            by_stream.setdefault(event['stream'], []).append(event)
        return {
            stream: (StreamingSTTService._join_finals(events), [l for e in events if e.get('is_final') for l in e.get('languages', [])])
            for stream, events in by_stream.items()
        }

    @staticmethod
    def choose_text(results: dict[str, tuple[str, list[str]]], languages: tuple[str, ...], state_language: str | None = None) -> str:
        """
        Chooses the text among the streams of `auto` and of the forced `languages`.
        A stream forced to a wrong language mostly gives nothing, so the only non-empty one is the right one;
        Nemotron gives no probabilities of the languages, and the confidence of the words is always 1.
        """
        def allowed(code: str) -> bool:
            return any(code.lower().startswith(language.lower()) for language in languages)

        auto_text, auto_languages = results.get('auto', ('', []))
        if len(auto_languages) > 0 and allowed(auto_languages[0]):
            return auto_text
        candidates = [language for language in languages if results.get(language, ('', []))[0] != '']
        if len(candidates) > 1 and state_language is not None:
            candidates = [c for c in candidates if c.lower().startswith(state_language.lower())] or candidates
        if len(candidates) > 0:
            return results[candidates[0]][0]
        # The language of `auto` is unknown rather than wrong
        return auto_text if len(auto_languages) == 0 else ''
