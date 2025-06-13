from kaia.kaia import SingleLineKaiaSkill, KaiaLog
from eaglesong.templates import *

class LogFeedbackIntents(TemplatesCollection):
    report = Template("Something is wrong", "You're misbehaving")

class LogFeedbackReplies(TemplatesCollection):
    answer = Template("The log entry has been created. I'm sorry for that.")

class LogFeedbackSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(LogFeedbackIntents, LogFeedbackReplies)

    def run(self):
        input: Utterance = yield
        KaiaLog.write('VocalFeedback', str(dict(intent=input.template.name)))
        yield LogFeedbackReplies.answer.utter()
