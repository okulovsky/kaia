from typing import *
from eaglesong.core import Translator, TranslatorOutputPackage
from kaia.avatar import AvatarApi, TextLike
from kaia.dub import Utterance, UtterancesSequence


class VoiceoverTranslator(Translator):
    def __init__(self,
                 inner_function,
                 avatar_api: Optional[AvatarApi],
                 ):
        self.avatar_api = avatar_api

        super(VoiceoverTranslator, self).__init__(
            inner_function,
            output_generator_translator=self.translate_outgoing
        )

    def _to_audio(self, s: TextLike):
        if self.avatar_api is None:
            if isinstance(s, str):
                yield s
            elif isinstance(s, Utterance):
                yield s.to_str()
            elif isinstance(s, UtterancesSequence):
                yield " ".join(u.to_str() for u in s.utterances)
            else:
                yield str(s)
        else:
            result = self.avatar_api.dub(s)
            yield result.full_text
            for job in result.jobs:
                yield self.avatar_api.dub_get_result(job)



    def translate_outgoing(self, o: TranslatorOutputPackage):
        if (
                isinstance(o.inner_output, Utterance)
                or isinstance(o.inner_output, str)
                or isinstance(o.inner_output, UtterancesSequence)
        ):
            yield from self._to_audio(o.inner_output)
        else:
            yield o.inner_output











