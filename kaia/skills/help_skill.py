from typing import *
from kaia.kaia import KaiaAssistant, SingleLineKaiaSkill, Message
from eaglesong.templates import *

class HelpIntents(TemplatesCollection):
    help = Template("What can you do?")

class HelpReplies(TemplatesCollection):
    help = (
        Template("Here is the list of available commands")
        .no_paraphrasing()
    )

class HelpSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(HelpIntents, HelpReplies)
        self.assistant: Optional[KaiaAssistant] = None

    def run(self):
        if self.assistant is None:
            raise ValueError("Skill is misconfigured, no assistant is provided")
        reply = []
        for skill in self.assistant.skills:
            commands = ', '.join(template for intent in skill.get_intents() for template in intent.string_templates)
            reply.append(f'{skill.get_name()}: {commands}')
            reply.append('')
        yield Message(Message.Type.ToUser, '\n'.join(reply))
        yield HelpReplies.help.utter()



