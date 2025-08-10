import random
from ...daemon import SoundLevel, StateChange, MicState, PlayStarted, SilenceLevelSet
from avatar.known_messages import SoundConfirmation

class SampleGenerator:
    def __init__(self):
        self.last_sound_command: PlayStarted|None = None

    def __call__(self, data):
        data.append(SoundLevel(random.random()).ensure_envelop())

        if random.random()<0.1:
            data.append(SilenceLevelSet(0.1+random.random()*0.1))

        if random.random() < 0.1:
            data.append(StateChange(state=MicState(random.randint(0, 3))).ensure_envelop())

        if self.last_sound_command is None:
            if random.random() < 0.3:
                self.last_sound_command = PlayStarted(random.randint(100, 200))
                data.append(self.last_sound_command)
        else:
            if random.random() < 0.3:
                data.append(SoundConfirmation().as_confirmation_for(self.last_sound_command))
                self.last_sound_command = None

