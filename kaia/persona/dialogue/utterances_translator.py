from typing import *
from ...eaglesong.core import Translator, Audio, TranslatorInputPackage, TranslatorOutputPackage
from ..dub.core import Dubber, RhasspyAPI, Template, Utterance


def prettify_utterance(previous_str, utterance: Utterance):
    s = previous_str
    if len(s) > 0:
        s += ' '
    return s+utterance.template.to_str(utterance.value)

class UtterancesTranslator(Translator):
    def __init__(self,
                 inner_function,
                 rhasspy_api: RhasspyAPI,
                 dubber: Optional[Dubber] = None,
                 fake_audio = False
                 ):
        self.dubber = dubber
        self.rhasspy_api = rhasspy_api
        self.handler = self.rhasspy_api.handler
        self.fake_audio = fake_audio
        super(UtterancesTranslator, self).__init__(
            inner_function,
            None,
            self.translate_incoming,
            None,
            self.translate_outgoing
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

    def utterances_to_audio_or_text(self, utterances: Union[Utterance, Iterable[Utterance]]):
        if isinstance(utterances, Utterance):
            utterances = [utterances]
        s = ''
        for u in utterances:
            s = prettify_utterance(s, u)
        if self.dubber is None:
            return s
        if self.fake_audio:
            files = self.dubber.decompose(utterances)
            return Audio(files, s)
        else:
            return self.dubber.dub_to_audio(utterances)


    def translate_outgoing(self, o: TranslatorOutputPackage):
        if isinstance(o.inner_output, Utterance):
            return self.utterances_to_audio_or_text(o.inner_output)
        elif isinstance(o.inner_output, Iterable):
            l = list(o.inner_output)
            if all(isinstance(t, Utterance) for t in l):
                return self.utterances_to_audio_or_text(o.inner_output)
        else:
            return o.inner_output











