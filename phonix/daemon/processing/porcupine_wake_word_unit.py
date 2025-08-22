from avatar.messaging import StreamClient
from .core import IUnit, State, MicState, SystemSoundCommand, SystemSoundType
from avatar.daemon import WakeWordEvent

import pvporcupine

class PorcupineWakeWordUnit(IUnit):
    def __init__(self, keyword: str = 'computer'):
        self.keyword = keyword
        self.porcupine = None

    def process(self, data: IUnit.Input) -> State|None:
        if self.porcupine is None:
            self.porcupine = pvporcupine.create(keywords=[self.keyword])
        if data.state.mic_state != MicState.Standby:
            return None
        keyword_index = self.porcupine.process(data.mic_data.buffer)
        if keyword_index < 0 and not data.open_mic_requested:
            return None
        if keyword_index >= 0:
            data.send_message(WakeWordEvent(self.keyword))

        data.send_message(SystemSoundCommand(SystemSoundType.opening))
        return State(MicState.Opening)

