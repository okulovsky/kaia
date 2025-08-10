from typing import cast
from kaia import World, SingleLineKaiaSkill, KaiaContext
from grammatron import *
from eaglesong import ContextRequest
from avatar.daemon import SpeakerIdentificationService

USER = VariableDub('user')

class RecognitionFeedbackIntents(TemplatesCollection):
    misrecognition = Template(f"I'm actually {USER}")


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
        substitution = RecognitionFeedbackIntents.misrecognition.substitute(**{USER.name: VariableDub(USER.name, OptionsDub(users))})
        intents = RecognitionFeedbackIntents.get_templates(substitution)
        super().__init__(intents, RecognitionFeedbackAnswers)

    def run(self):
        input: Utterance = yield
        actual_speaker = input.get_field()
        context = yield ContextRequest()
        context = cast(KaiaContext, context)

        report = context.get_client().run_synchronously(
            SpeakerIdentificationService.Train(actual_speaker),
            SpeakerIdentificationService.TrainConfirmation,
            10
        )
        if report.admit_errors:
            yield RecognitionFeedbackAnswers.sorry()
        else:
            yield RecognitionFeedbackAnswers.i_know()



