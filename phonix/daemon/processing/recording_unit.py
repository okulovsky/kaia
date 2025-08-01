from .core import IUnit, State, MicState, UnitInput, SystemSoundType, SystemSoundCommand
from ..recording_server import RecordingApi, RecordingRequest
from avatar.services import SoundEvent
from uuid import uuid4
from .sound_buffer import SoundBuffer


class RecordingUnit(IUnit):
    def __init__(self, api: RecordingApi, buffer_length_in_seconds):
        self.api = api
        self.current_request: RecordingRequest|None = None
        self.buffer = SoundBuffer(buffer_length_in_seconds)
        self.current_file_name: str|None = None

    def process(self, incoming_data: UnitInput) -> State|None:
        if self.current_request is None:
            self.buffer.add(incoming_data.mic_data)

        if incoming_data.state.mic_state == MicState.Recording:
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
        elif incoming_data.state.mic_state == MicState.Sending:
            if self.api is not None:
                self.current_request.send()
                self.current_request = None
                self.buffer.clear()
            incoming_data.client.put(SystemSoundCommand(SystemSoundCommand.Type.confirmation))
            incoming_data.client.put(SoundEvent(self.current_file_name))
            self.current_file_name = None
            return State(MicState.Standby)

        return None