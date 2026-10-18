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
                 ):
        self.state = state
        self.cache_folder = Path(cache_folder)
        self.default_request = default_request if default_request is not None else TemplatesRecognitionRequest()
        self.nemotron_model = nemotron_model
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
        task = (
            Nemotron
            .new_task(id=event.file_id.split('.')[0] + '.nemotron-stream')
            .transcribe_stream(event.file_id, language=language, model=self.nemotron_model)
        )
        try:
            result = self.client.run_synchronously(BrainBoxService.Command(task).as_reply_to(event), BrainBoxService.Confirmation)
            if result.result is None:
                raise ValueError(f"Expected result, error\n{result.error}")
            text = self.read_final_text((self.cache_folder / result.result).read_bytes())
        except Exception:
            # A cancelled recording is deleted while it is read, and the job fails: the request is still pending
            if self.requested is None and request is not self.default_request:
                self.requested = request
            return NLUTextEvent(event.file_id, None, request, traceback.format_exc())
        return NLUTextEvent(event.file_id, text, request)

    @staticmethod
    def read_final_text(content: bytes) -> str:
        events = [json.loads(line) for line in content.decode('utf-8').splitlines() if line.strip() != '']
        finals = [e for e in events if e.get('is_final')]
        if len(finals) == 0:
            finals = events[-1:]
        return ' '.join(e['text'].strip() for e in finals if e['text'].strip() != '')
