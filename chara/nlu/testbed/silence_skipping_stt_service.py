import wave
from pathlib import Path
import numpy as np
from avatar.daemon import WhisperKenLMSTTService, BrainBoxService, NLUTextEvent, State
from avatar.daemon.common import SoundEvent, message_handler


def loudest_window_level(path: Path, window: int = 512) -> float:
    """RMS of the loudest window of the wav, from 0 to 1"""
    with wave.open(str(path)) as file:
        samples = np.frombuffer(file.readframes(file.getnframes()), dtype=np.int16) / 32768
    if len(samples) < window:
        return float(np.sqrt((samples ** 2).mean())) if len(samples) > 0 else 0.0
    windows = samples[:len(samples) // window * window].reshape(-1, window)
    return float(np.sqrt((windows ** 2).mean(axis=1)).max())


class SilenceSkippingWhisperKenLMSTTService(WhisperKenLMSTTService):
    """
    Whisper hears "Thank you." in a recording without speech, e.g. when a click opened the recording.
    Such recordings are recognized as an empty text without Whisper.
    """
    def __init__(self, state: State, cache_folder: Path, min_level: float = 0.05, **kwargs):
        super().__init__(state, **kwargs)
        self.cache_folder = Path(cache_folder)
        self.min_level = min_level

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def transcribe(self, event: SoundEvent) -> NLUTextEvent:
        if loudest_window_level(self.cache_folder / event.file_id) >= self.min_level:
            return super().transcribe(event)
        request = self.requested if self.requested is not None else self.default_request
        self.requested = None
        return NLUTextEvent(event.file_id, '', request)
