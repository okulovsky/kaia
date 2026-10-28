import traceback
from brainbox.deciders import WhisperKenLM
from ..common import message_handler, AvatarService, State, SoundEvent
from ..brainbox_service import BrainBoxService
from ..stt_service import IRecognitionRequest, TemplatesRecognitionRequest, FreeSpeechRecognitionRequest
from .nlu_text_event import NLUTextEvent


class WhisperKenLMSTTService(AvatarService):
    def __init__(self,
                 state: State,
                 default_request: IRecognitionRequest|None = None,
                 kenlm_weight: float = 0.5,
                 beams: int = 5,
                 languages: tuple[str, ...] | None = ('en', 'de', 'ru'),
                 ):
        self.state = state
        self.default_request = default_request if default_request is not None else TemplatesRecognitionRequest()
        self.kenlm_weight = kenlm_weight
        self.beams = beams
        self.languages = languages
        self.requested: IRecognitionRequest|None = None

    def requires_brainbox(self):
        return True

    @message_handler
    def request(self, message: IRecognitionRequest) -> None:
        self.requested = message

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def transcribe(self, event: SoundEvent) -> NLUTextEvent:
        request = self.default_request
        if self.requested is not None:
            request = self.requested
            self.requested = None
        languages = list(self.languages) if self.languages else None
        if isinstance(request, FreeSpeechRecognitionRequest):
            language = request.language or self.state.language
            if language is not None:
                languages = [language]
        task = (
            WhisperKenLM
            .new_task(id=event.file_id.split('.')[0] + '.whisper-kenlm')
            .transcribe(file=event.file_id, weight=self.kenlm_weight, beams=self.beams, languages=languages)
        )
        try:
            result = self.client.run_synchronously(BrainBoxService.Command(task).as_reply_to(event), BrainBoxService.Confirmation)
            if result.result is None:
                raise ValueError(f"Expected result, error\n{result.error}")
        except Exception:
            return NLUTextEvent(event.file_id, None, request, traceback.format_exc())
        return NLUTextEvent(event.file_id, str(result.result), request)
