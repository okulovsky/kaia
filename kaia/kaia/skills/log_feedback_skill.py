from kaia.kaia.core import KaiaContext, SingleLineKaiaSkill
from kaia.eaglesong.core import ContextRequest
from kaia.avatar.dub.languages.en import *

class LogFeedbackIntents(TemplatesCollection):
    report = Template("Something is wrong", "You're misbehaving")

class LogFeedbackReplies(TemplatesCollection):
    answer = Template("The log entry has been created. I'm sorry for that.")

class LogFeedbackSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(LogFeedbackIntents, LogFeedbackReplies)

    def run(self):
        context: KaiaContext = yield ContextRequest()
        if context.driver is None:
            raise ValueError("The service is misconfigured: `driver` is missing from KaiaContext")
        input: Utterance = yield
        context.driver.log_writer.write('VocalFeedback', dict(intent=input.template.name))
        yield LogFeedbackReplies.answer.utter()
