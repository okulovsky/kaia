from typing import cast, ClassVar
from kaia import World, SingleLineKaiaSkill, KaiaContext, UserIdentification
from grammatron import *
from eaglesong import ContextRequest
from avatar.daemon import SpeakerIdentificationService, UserWalkInService
from typing import Callable
from datetime import datetime

USER = VariableDub('user')

class RecognitionFeedbackIntents(TemplatesCollection):
    misrecognition: ClassVar[Template] = Template(f"I'm actually {USER}")


class RecognitionFeedbackReplies(TemplatesCollection):
    i_know: ClassVar[Template] = (
        Template("Yeah, I know")
        .context(
            f"{World.user} said {World.character} misrecognized {World.user.pronoun}, but it was actually not the case",
            reply_to=RecognitionFeedbackIntents.misrecognition
        )
    )

    fix_audio: ClassVar[Template] = (
        Template("Sorry I misrecognized your voice, I'll remember better next time")
        .context(
            f"{World.character} confused {World.user} with someone else by {World.user.pronoun.possessive} voice and now apologizes for the error",
            reply_to=RecognitionFeedbackIntents.misrecognition
        )
    )

    fix_image: ClassVar[Template] = (
        Template("Sorry I misrecognized your face, I'll remember better next time")
        .context(
            f"{World.character} confused {World.user} with someone else by {World.user.pronoun.possessive} face and now apologizes for the error",
            reply_to=RecognitionFeedbackIntents.misrecognition
        )
    )


    error: ClassVar[Template] = (
        Template("We haven't spoken lately")
        .context(
            f"{World.user} said {World.character} misrecognized {World.user.pronoun}, but they didn't spoke lately, so it's a misunderstanding",
            reply_to=RecognitionFeedbackIntents.misrecognition
        )
    )

class RecognitionFeedbackSkill(SingleLineKaiaSkill):
    def __init__(self,
                 users: list[str],
                 maximum_time_margin_in_seconds: int = 5*60,
                 datetime_factory: Callable[[], datetime] = datetime.now
                 ) -> None:
        substitution = RecognitionFeedbackIntents.misrecognition.substitute(**{USER.name: OptionsDub(users)})
        intents = RecognitionFeedbackIntents.get_templates(substitution)
        self.maximum_time_margin_in_seconds = maximum_time_margin_in_seconds
        self.datetime_factory = datetime_factory
        super().__init__(intents, RecognitionFeedbackReplies)

    def run(self):
        input: Utterance = yield
        actual_speaker = input.get_field()
        context = yield ContextRequest()
        context = cast(KaiaContext, context)

        if context.previous_identification is None:
            yield RecognitionFeedbackReplies.error()
            return

        ident = context.previous_identification

        current_time = self.datetime_factory()
        timedelta = current_time - ident.timestamp
        if timedelta.total_seconds() > self.maximum_time_margin_in_seconds:
            yield RecognitionFeedbackReplies.error()
            return

        if ident.user == actual_speaker:
            yield RecognitionFeedbackReplies.i_know()
            return

        if ident.type == UserIdentification.Type.Voice:
            yield SpeakerIdentificationService.Train(ident.file_id, actual_speaker)
            yield RecognitionFeedbackReplies.fix_audio()
        elif ident.type == UserIdentification.Type.Image:
            yield UserWalkInService.Train(ident.file_id, actual_speaker)
            yield RecognitionFeedbackReplies.fix_image()



