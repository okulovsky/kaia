from kaia import KaiaSkillBase, ErrorAnnouncement, World, WhisperOpenMicListen
from loguru import logger
from grammatron import *

class LogFeedbackIntents(TemplatesCollection):
    report = Template("Something is wrong", "You're misbehaving")

class LogFeedbackReplies(TemplatesCollection):
    report_request = Template("Tell me what happened").context(f"{World.user} have just complained about an error, and {World.character} asks what exactly has happened to provide a report.")
    confirmation = Template("The log entry has been created. I'm sorry for that.").context(f'{World.user} explained what was the error, and now {World.character} confirms filing the report and apoligizes.')


class LogFeedbackSkill(KaiaSkillBase):
    def __init__(self,
                 ):
        super().__init__(
            LogFeedbackIntents,
            LogFeedbackReplies
        )


    def should_start(self, input) -> False:
        if not isinstance(input, Utterance):
            return False
        if input not in LogFeedbackIntents.report:
            return False
        return True

    def should_proceed(self, input) -> False:
        return isinstance(input, str)

    def run(self):
        yield LogFeedbackReplies.report_request()
        s = yield WhisperOpenMicListen()
        logger.error(f"Error is reported by user {s}")
        yield ErrorAnnouncement(s)
        yield LogFeedbackReplies.confirmation()






