from typing import *
from kaia.kaia.core import KaiaAssistant, SingleLineKaiaSkill, KaiaMessage
from kaia.avatar.dub.languages.en import *

class HelpIntents(TemplatesCollection):
    help = Template("What can you do?")

class HelpReplies(TemplatesCollection):
    help = Template("Here is the list of available commands")

class HelpSkill(SingleLineKaiaSkill):
    def __init__(self):
        super().__init__(HelpIntents, HelpReplies)
        self.assistant: Optional[KaiaAssistant] = None

    def run(self):
        if self.assistant is None:
            raise ValueError("Skill is misconfigured, no assistant is provided")
        reply = []
        for skill in self.assistant.skills:
            reply.append(skill.get_name())
            for intent in skill.get_intents():
                for template in intent.string_templates:
                    reply.append("- "+template)
            reply.append('')
        yield KaiaMessage(True, '\n'.join(reply))
        yield HelpReplies.help.utter()



