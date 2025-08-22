from datetime import datetime
from .core import IUnit, UnitInput, State, MicState, SystemSoundCommand


class TooLongOpenMicUnit(IUnit):
    def __init__(self, open_mic_time_limit_in_seconds: float):
        self.opening_time: datetime|None = None
        self.open_mic_time_limit_in_seconds = open_mic_time_limit_in_seconds

    def process(self, incoming_data: UnitInput) -> State|None:
        if incoming_data.state.mic_state != MicState.Open:
            self.opening_time = None
        else:
            if self.opening_time is None:
                self.opening_time = datetime.now()
            elif (datetime.now()-self.opening_time).total_seconds() > self.open_mic_time_limit_in_seconds:
                incoming_data.send_message(SystemSoundCommand(SystemSoundCommand.Type.error))
                return State(MicState.Standby)



