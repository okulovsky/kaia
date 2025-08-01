from __future__ import annotations

import threading
import time
from avatar.messaging import StreamClient
from avatar.services import SoundInjectionCommand, SoundCommand, SoundConfirmation

from ..processing import IUnit, SystemSoundCommand, SystemSoundType, State, MicState, UnitInput
from ..outputs import IAudioOutput
from ..inputs import IAudioInput, FakeInput
from .events import *
from pathlib import Path
from yo_fluq import FileIO
from .messages_translator import MessagesTranslator



class PhonixDeamon:
    def __init__(self,
                 client: StreamClient,
                 file_retriever: Optional[Callable[[str],bytes]],
                 input: IAudioInput,
                 output: IAudioOutput,
                 units: list[IUnit],
                 system_sounds: dict[SystemSoundType, bytes],
                 external_client: StreamClient
                ):
        self.client = client
        self.file_retriever = file_retriever
        self.input: IAudioInput = input
        self.output = output
        self.units = [(self.client.clone(), unit) for unit in units]
        self.system_sounds = system_sounds
        self.confirm_on_play_finishes: List[IMessage,...]|None = None
        self.confirm_on_injection_finishes: IMessage|None = None
        self.state = State(MicState.Standby)
        self._termination_requested = threading.Event()
        if external_client is not None:
            self.translator = MessagesTranslator(self.client, external_client)
        else:
            self.translator = None


    def confirm_currently_playing(self, terminated: bool):
        for message in self.confirm_on_play_finishes:
            self.client.put(SoundConfirmation(terminated).as_confirmation_for(message))
        self.confirm_on_play_finishes = None

    def start_playing(self, content, external_message, internal_message):
        if self.output.is_playing():
            self.output.cancel_playing()
            self.confirm_currently_playing(True)
        self.client.put(internal_message)
        self.output.start_playing(content)
        self.confirm_on_play_finishes = [external_message, internal_message]

    def parse_incoming_message(self, message):
        if isinstance(message, SoundCommand):
            content = self.file_retriever(message.file_id)
            self.start_playing(content, message, PlayStarted(message.text))
        if isinstance(message, SoundInjectionCommand):
            if not isinstance(self.input, FakeInput):
                self.input.stop()
                self.input = FakeInput()
            content = self.file_retriever(message.file_id)
            self.confirm_on_injection_finishes = message
            self.input.set_sample(content)
        if isinstance(message, SystemSoundCommand):
            if message.sound in self.system_sounds:
                self.start_playing(self.system_sounds[message.sound], message, PlayStarted(message.sound.name))


    def iteration(self):
        if self.translator is not None:
            self.translator.iteration()
        messages = self.client.pull()
        for message in messages:
            self.parse_incoming_message(message)
        if not self.output.is_playing() and self.confirm_on_play_finishes is not None:
            self.confirm_currently_playing(False)


        if isinstance(self.input, FakeInput) and self.input.is_buffer_empty() and self.confirm_on_injection_finishes is not None:
            self.client.put(self.confirm_on_injection_finishes.confirm_this())
            self.confirm_on_injection_finishes = None

        mic_data = self.input.read()

        for client, unit in self.units:
            state_change = unit.process(UnitInput(self.state, mic_data, client))
            if state_change is not None:
                self.state = state_change
                self.client.put(StateChange(state_change.mic_state))

    def run(self):
        self.input.start()
        try:
            while not self._termination_requested.is_set():
                self.iteration()
                time.sleep(0.01)
        finally:
            self.input.stop()


    def terminate(self):
        self._termination_requested.set()


    @staticmethod
    def get_default_system_sounds() -> dict[SystemSoundType, bytes]:
        result = {}
        path = Path(__file__).parent/'files'
        result[SystemSoundType.opening] = FileIO.read_bytes(path/'beep_hi.wav')
        result[SystemSoundType.confirmation] = FileIO.read_bytes(path / 'beep_lo.wav')
        result[SystemSoundType.error] = FileIO.read_bytes(path / 'beep_error.wav')
        return result








