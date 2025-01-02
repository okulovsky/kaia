from typing import *
from ..driver import AudioCommand
from .partial_listen_translator import PartialListenTranslator
from kaia.avatar import AvatarApi, RecognitionSettings


class RecognitionTranslator(PartialListenTranslator):
    def __init__(self,
                 inner_function,
                 avatar_api : AvatarApi,
                 ):
        self.avatar_api = avatar_api
        super().__init__(
            inner_function,
            RecognitionSettings,
            call_input_translate_without_payload=True
        )

    def captures_input(self, input):
        return isinstance(input, AudioCommand)

    def on_translate_input(self, payload: Optional[RecognitionSettings], input: Any):
        if payload is None:
            payload = RecognitionSettings(RecognitionSettings.NLU.Rhasspy)
        return self.avatar_api.recognition_transcribe(input.id, payload)



