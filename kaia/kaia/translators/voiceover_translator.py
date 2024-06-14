from typing import *
from kaia.eaglesong.core import Translator, Audio, TranslatorInputPackage, TranslatorOutputPackage
from kaia.avatar.dub.core import RhasspyAPI, Utterance
from kaia.avatar.server import AvatarAPI


class VoiceoverTranslator(Translator):
    def __init__(self,
                 inner_function,
                 avatar_api: Optional[AvatarAPI],
                 ):
        self.avatar_api = avatar_api

        super(VoiceoverTranslator, self).__init__(
            inner_function,
            None,
            None,
            None,
            self.translate_outgoing
        )

    def utterances_to_audio_or_text(self, utterance: Utterance):
        s = utterance.to_str()
        if self.avatar_api is not None:
            return self.avatar_api.dub_utterance(utterance)
        else:
            return s

    def str_to_audio_or_text(self, s: str):
        if self.avatar_api is not None:
            return self.avatar_api.dub_string(s)
        else:
            return s


    def translate_outgoing(self, o: TranslatorOutputPackage):
        if isinstance(o.inner_output, Utterance):
            return self.utterances_to_audio_or_text(o.inner_output)
        elif isinstance(o.inner_output, str):
            return self.str_to_audio_or_text(o.inner_output)
        else:
            return o.inner_output











