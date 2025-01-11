from typing import *
from kaia.dub.languages.en import *
from kaia.kaia import SingleLineKaiaSkill, KaiaContext
from eaglesong import ContextRequest

class RecognitionFeedbackIntents(TemplatesCollection):
    misrecognition = Template("I'm actually {user}", user=ToStrDub())


class RecognitionFeedbackAnswers(TemplatesCollection):
    i_know = Template("Yeah, I know")
    sorry = Template("Sorry I misrecognized you")

class RecognitionFeedbackSkill(SingleLineKaiaSkill):
    def __init__(self, users: list[str]):
        substitution = dict(user=StringSetDub(users))
        self.intents: Type[RecognitionFeedbackIntents] = RecognitionFeedbackIntents.substitute(substitution)
        super().__init__(self.intents, RecognitionFeedbackAnswers)

    def run(self):
        input: Utterance = yield
        actual_speaker = input.get_field()
        context: KaiaContext = yield ContextRequest()
        avatar_api = context.avatar_api
        was_fixed = avatar_api.recognition_speaker_fix(actual_speaker)
        if was_fixed:
            yield RecognitionFeedbackAnswers.sorry()
        else:
            yield RecognitionFeedbackAnswers.i_know()



