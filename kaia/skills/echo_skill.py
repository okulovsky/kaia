from typing import *
from kaia import KaiaSkillBase, World, WhisperOpenMicListen
from grammatron import Template, Utterance, TemplatesCollection




class EchoIntents(TemplatesCollection):
    echo = Template("Repeat after me!")


class EchoReplies(TemplatesCollection):
    echo_request = (
        Template("Say anything and I will repeat")
        .context(
            f"{World.user} asks {World.character} to reply whatever {World.user} says, and {World.character} agrees to play this game.",
            reply_to=EchoIntents.echo
        )
    )


class EchoSkill(KaiaSkillBase):
    def __init__(self,
                 ):
        super().__init__(EchoIntents, EchoReplies)

    def should_start(self, input) -> False:
        if not isinstance(input, Utterance):
            return False
        if input not in EchoIntents.echo:
            return False
        return True

    def should_proceed(self, input) -> False:
        return isinstance(input, str)

    def run(self):
        yield EchoReplies.echo_request()
        s = yield WhisperOpenMicListen()
        yield s





