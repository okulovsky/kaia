from typing import *
from avatar import World
from eaglesong.templates import *
from kaia.kaia import SingleLineKaiaSkill, KaiaContext
from eaglesong import ContextRequest

class RecognitionFeedbackIntents(TemplatesCollection):
    misrecognition = Template(f"I'm actually {TemplateVariable('user')}")


class RecognitionFeedbackAnswers(TemplatesCollection):
    i_know = (
        Template("Yeah, I know")
        .context(
            f"{World.user} said {World.character} misrecognized {World.user.pronoun}, but it was actually not the case",
            reply_to=RecognitionFeedbackIntents.misrecognition
        )
    )

    sorry = (
        Template("Sorry I misrecognized you")
        .context(
            f"{World.character} confused {World.user} with someone else and now apoligizes for the error",
            reply_to=RecognitionFeedbackIntents.misrecognition
        )
    )

class RecognitionFeedbackSkill(SingleLineKaiaSkill):
    def __init__(self, users: list[str]):
        substitution = RecognitionFeedbackIntents.misrecognition.substitute(user = OptionsDub(users))
        intents = RecognitionFeedbackIntents.get_templates(substitution)
        super().__init__(intents, RecognitionFeedbackAnswers)

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



