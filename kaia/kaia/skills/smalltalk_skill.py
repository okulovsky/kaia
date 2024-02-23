from typing import *
from kaia.kaia.core import SingleLineKaiaSkill
from kaia.avatar.dub.core import TemplatesCollection, Utterance


class SmalltalkSkill(SingleLineKaiaSkill):
    def __init__(self,
                 intents: Type[TemplatesCollection],
                 replies: Type[TemplatesCollection]):
        super().__init__(intents, replies)
        self.replies = replies


    def run(self):
        input: Utterance = yield
        for reply in self.replies.get_templates():
            if reply.reply_to.name == input.template.name:
                yield reply.utter()
                break

