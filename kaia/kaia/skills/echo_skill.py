from typing import *
from ..core import IKaiaSkill
from ...avatar.dub.core import Template, Utterance, TemplatesCollection
from ..translators import Listen

class EchoIntents(TemplatesCollection):
    echo = Template("Repeat after me!")


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
        s = yield Listen().open_mic()
        yield s


