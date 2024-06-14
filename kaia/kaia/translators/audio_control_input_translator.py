from typing import *
from kaia.eaglesong.core import Translator, TranslatorInputPackage
from kaia.kaia.audio_control import AudioControlData
from kaia.avatar.dub.core import RhasspyAPI



class AudioControlInputTranslator(Translator):
    def __init__(self,
                 inner_function,
                 rhasspy_api: Optional[RhasspyAPI],
                 ):
        self.rhasspy_api = rhasspy_api

        super(AudioControlInputTranslator, self).__init__(
            inner_function,
            None,
            self.translate_incoming,
            None,
            None
        )

    def translate_incoming(self, i: TranslatorInputPackage):
        if not isinstance(i.outer_input, AudioControlData):
            return i.outer_input
        if i.outer_input.source == 'whisper':
            return i.outer_input.payload
        elif i.outer_input.source == 'rhasspy':
            return self.rhasspy_api.handler.parse_json(i.outer_input.payload)
        else:
            raise ValueError(f'Source of type AudioControlData had unknown source {i.outer_input.source}')










