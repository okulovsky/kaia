from .core import IUnit, State, MicState, UnitInput, SystemSoundType, SystemSoundCommand
from avatar.daemon import SoundEvent
from uuid import uuid4
from .sound_buffer import SoundBuffer


class RecordingUnit(IUnit):
    def __init__(self, api, buffer_length_in_seconds):
        self.api = api
        self.current_request: None = None
        self.buffer_length_in_seconds = buffer_length_in_seconds
        self.current_file_name: str|None = None
        self.buffer: SoundBuffer|None = None

    def process(self, incoming_data: UnitInput) -> State|None:
        if incoming_data.state.mic_state == MicState.Open:
            if self.buffer is None:
                self.buffer = SoundBuffer(self.buffer_length_in_seconds)
            self.buffer.add(incoming_data.mic_data)
        elif incoming_data.state.mic_state == MicState.Recording:
            if self.current_file_name is None:
                self.current_file_name = str(uuid4()) + '.wav'
            if self.api is not None:
                if self.current_request is None:
                    self.current_request = self.api.create_recording_request(
                        self.current_file_name,
                        incoming_data.mic_data.sample_rate,
                        self.buffer.buffer
                    )
                else:
                    self.current_request.add_wav_data(incoming_data.mic_data.buffer)
            self.buffer = None
        elif incoming_data.state.mic_state == MicState.Sending:
            if self.api is not None:
                self.current_request.send()
                self.current_request = None
            incoming_data.send_message(SystemSoundCommand(SystemSoundCommand.Type.confirmation))
            incoming_data.send_message(SoundEvent(self.current_file_name))
            self.current_file_name = None
            return State(MicState.Standby)
        else:
            self.buffer = None
