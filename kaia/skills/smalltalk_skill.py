from typing import *
from kaia.kaia import SingleLineKaiaSkill
from eaglesong.templates import TemplatesCollection, Utterance


class SmalltalkSkill(SingleLineKaiaSkill):
    def __init__(self,
                 intents: Type[TemplatesCollection],
                 replies: Type[TemplatesCollection]):
        super().__init__(intents, replies)
        self.replies = replies


    def run(self):
        input: Utterance = yield
        for reply in self.replies.get_templates():
            reply_to = reply.get_context().reply_to
            if reply_to is None:
                raise ValueError(f'`reply_to` not sent for `{reply.get_name()}`')
            for repl in reply_to:
                if repl.get_name() == input.template.get_name():
                    yield reply.utter()
                    return

