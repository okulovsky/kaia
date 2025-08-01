from avatar.messaging import StreamClient
from .core import IUnit, State, MicState, SystemSoundCommand, SystemSoundType
from avatar.services import WakeWordEvent

import pvporcupine

class PorcupineWakeWordUnit(IUnit):
    def __init__(self, keyword: str = 'computer'):
        self.keyword = keyword
        self.porcupine = pvporcupine.create(keywords=[self.keyword])

    def process(self, data: IUnit.Input) -> State|None:
        if data.state.mic_state != MicState.Standby:
            return None
        keyword_index = self.porcupine.process(data.mic_data.buffer)
        if keyword_index < 0:
            return None
        data.client.put(WakeWordEvent(self.keyword))
        data.client.put(SystemSoundCommand(SystemSoundType.opening))
        return State(MicState.Open)

