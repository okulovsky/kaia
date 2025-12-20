import pvporcupine

from avatar.messaging import StreamClient
from .core import IUnit, State, MicState, SystemSoundCommand, SystemSoundType
from avatar.daemon import WakeWordEvent
from yo_fluq import FileIO

import numpy as np
import os


class PorcupineWakeWordUnitNewVersion(IUnit):
    """
    Wake-word detection using Porcupine 2.x
    """

    def __init__(self, config_location: str):
        self.config_location = config_location
        self.porcupine = None
        self._buffer = []  # internal aggregator buffer for int samples

    def _init_porcupine(self):
        from pvporcupine import Porcupine
        data = FileIO.read_json(self.config_location)

        self.porcupine = pvporcupine.create(
            **data
        )

    def _enqueue_audio(self, samples: list[int]) -> list[np.ndarray]:
        """
        Add new audio samples to internal buffer and emit
        full frames of size porcupine.frame_length as numpy.int16 arrays.
        """

        # Append new samples
        self._buffer.extend(samples)

        frames = []
        frame_len = self.porcupine.frame_length

        # Extract as many full frames as possible
        while len(self._buffer) >= frame_len:
            chunk = self._buffer[:frame_len]
            del self._buffer[:frame_len]   # remove consumed samples
            frames.append(np.array(chunk, dtype=np.int16))

        return frames

    def process(self, data: IUnit.Input) -> State | None:
        # Initialize Porcupine
        if self.porcupine is None:
            self._init_porcupine()

        # Only listen when standby
        if data.state.mic_state != MicState.Standby:
            return None

        # Convert incoming list[int] to full porcupine frames
        frames = self._enqueue_audio(data.mic_data.buffer)

        wake_detected = False

        for frame in frames:
            result = self.porcupine.process(frame)
            if result >= 0:
                wake_detected = True
                break

        # No wake-word
        if not wake_detected and not data.open_mic_requested:
            return None

        # Wake-word found → notify
        if wake_detected:
            data.send_message(WakeWordEvent("porcupine"))

        # Open mic
        data.send_message(SystemSoundCommand(SystemSoundType.opening))
        return State(MicState.Opening)