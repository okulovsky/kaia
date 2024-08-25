from kaia.dub.languages.en import *
from kaia.kaia.core import SingleLineKaiaSkill
from kaia.kaia.translators import VolumeCommand

class VolumeIntents(TemplatesCollection):
    increase = Template(
        'Louder',
        'Increase the volume'
    )
    decrease = Template(
        'Quieter',
        'Decrease the volume'
    )

class VolumeReplies(TemplatesCollection):
    sound_check = Template('How does this sound?')

class VolumeSkill(SingleLineKaiaSkill):
    def __init__(self, delta: float = 0.1):
        self.delta = delta
        super().__init__(VolumeIntents, VolumeReplies)

    def run(self):
        input: Utterance = yield
        if input.template.name == VolumeIntents.increase.name:
            yield VolumeCommand(relative_value=self.delta)
            yield VolumeReplies.sound_check.utter()
        if input.template.name == VolumeIntents.decrease.name:
            yield VolumeCommand(relative_value=-self.delta)
            yield VolumeReplies.sound_check.utter()
