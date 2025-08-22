from kaia import World, SingleLineKaiaSkill, VolumeCommand
from kaia import VolumeControlService
from grammatron import *

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
    sound_check = Template('How does this sound?').context(
        reply_to=[VolumeIntents.increase, VolumeIntents.decrease],
        reply_details=f"{World.character} adjusts the volume and checks how it sounds."
    )

class VolumeSkill(SingleLineKaiaSkill):
    def __init__(self, delta: float = 0.1):
        self.delta = delta
        super().__init__(VolumeIntents, VolumeReplies)

    def run(self):
        input: Utterance = yield
        if input in VolumeIntents.increase:
            yield VolumeControlService.Command(relative_value=self.delta)
            yield VolumeReplies.sound_check.utter()
        if input in VolumeIntents.decrease:
            yield VolumeControlService.Command(relative_value=-self.delta)
            yield VolumeReplies.sound_check.utter()
