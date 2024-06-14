from typing import *
from kaia.eaglesong.core import Translator, Audio, TranslatorInputPackage
from kaia.avatar.dub.core import RhasspyAPI



class RhasspyInputTranslator(Translator):
    def __init__(self,
                 inner_function,
                 rhasspy_api: Optional[RhasspyAPI],
                 ):
        self.rhasspy_api = rhasspy_api
        self.handler = self.rhasspy_api.handler

        super(RhasspyInputTranslator, self).__init__(
            inner_function,
            None,
            self.translate_incoming,
            None,
            None
        )


    def text_to_utterance(self, s):
        ut =  self.handler.parse_string(s)
        if ut is None:
            return s
        return ut


    def audio_to_utterances(self, audio: Audio):
        if self.rhasspy_api is None:
            raise ValueError('Set `rhasspy_api` to recognize audio')
        return self.rhasspy_api.recognize(audio.data, True)


    def translate_incoming(self, i: TranslatorInputPackage):
        if isinstance(i.outer_input, str):
            return self.text_to_utterance(i.outer_input)
        elif isinstance(i.outer_input, Audio):
            return self.audio_to_utterances(i.outer_input)
        return i.outer_input











