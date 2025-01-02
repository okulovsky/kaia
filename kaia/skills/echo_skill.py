from typing import *
from ..kaia import IKaiaSkill, OpenMic
from kaia.dub.core import Template, Utterance, TemplatesCollection
from eaglesong import Listen
from kaia.avatar import RecognitionSettings, World


class EchoIntents(TemplatesCollection):
    echo = Template("Repeat after me!")


class EchoReplies(TemplatesCollection):
    echo_request = (
        Template("Say anything and I will repeat")
        .paraphrase(f"{World.user} asks {World.character} to reply whatever {World.user} says, and {World.character} agrees to play this game.")
    )


class EchoSkill(IKaiaSkill):
    def __init__(self,
                 ):
        pass

    def should_start(self, input) -> False:
        if not isinstance(input, Utterance):
            return False
        if input.template.name != EchoIntents.echo.name:
            return False
        return True

    def should_proceed(self, input) -> False:
        return isinstance(input, str)


    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.MultiLine

    def get_name(self) -> str:
        return 'Echo'

    def get_intents(self) -> Iterable[Template]:
        return [EchoIntents.echo]

    def get_runner(self):
        return self.run

    def run(self):
        yield "Say anything and I will repeat"
        s = (
            yield Listen()
            .store(RecognitionSettings(RecognitionSettings.NLU.Whisper))
            .store(OpenMic())
        )
        yield s





