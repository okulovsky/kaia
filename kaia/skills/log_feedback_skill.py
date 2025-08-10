from kaia import SingleLineKaiaSkill, ErrorAnnouncement
from loguru import logger
from grammatron import *

class LogFeedbackIntents(TemplatesCollection):
    report = Template("Something is wrong", "You're misbehaving")

class LogFeedbackReplies(TemplatesCollection):
    answer = Template("The log entry has been created. I'm sorry for that.")

class LogFeedbackSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(LogFeedbackIntents, LogFeedbackReplies)

    def run(self):
        logger.error('Error reported by user')
        yield ErrorAnnouncement()
        yield LogFeedbackReplies.answer.utter()
