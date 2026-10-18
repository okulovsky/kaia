import struct
import wave
import io
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import numpy as np
from grammatron import Utterance
from loguru import logger
from .common import message_handler, AvatarService, SoundEvent, SoundStreamingStartEvent, SoundStreamingEndEvent, TextEvent, TickEvent
from .stt_service import RecognitionEvent
from .speaker_identification_service import SpeakerIdentificationEvent


def _fix_wav_header(data: bytes) -> bytes:
    data = bytearray(data)
    data_size = len(data) - 44
    struct.pack_into('<I', data, 4, 36 + data_size)   # RIFF chunk size
    struct.pack_into('<I', data, 40, data_size)        # data chunk size
    return bytes(data)


def _resample_wav(data: bytes, target_rate: int) -> bytes:
    with wave.open(io.BytesIO(data)) as r:
        n_channels = r.getnchannels()
        sample_width = r.getsampwidth()
        src_rate = r.getframerate()
        frames = r.readframes(r.getnframes())

    if src_rate == target_rate:
        return data

    dtype = {1: np.int8, 2: np.int16, 4: np.int32}[sample_width]
    samples = np.frombuffer(frames, dtype=dtype).astype(np.float64)
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels)

    ratio = target_rate / src_rate
    n_out = int(len(samples) * ratio)
    x_old = np.linspace(0, 1, len(samples))
    x_new = np.linspace(0, 1, n_out)
    if n_channels > 1:
        resampled = np.column_stack([np.interp(x_new, x_old, samples[:, c]) for c in range(n_channels)])
    else:
        resampled = np.interp(x_new, x_old, samples)

    resampled = np.clip(resampled, np.iinfo(dtype).min, np.iinfo(dtype).max).astype(dtype)

    buf = io.BytesIO()
    with wave.open(buf, 'w') as w:
        w.setnchannels(n_channels)
        w.setsampwidth(sample_width)
        w.setframerate(target_rate)
        w.writeframes(resampled.tobytes())
    return buf.getvalue()


@dataclass
class _Recording:
    started_at: datetime
    finished_at: datetime|None = None
    fixed_file_id: str|None = None
    recognition: RecognitionEvent|None = None
    speaker: SpeakerIdentificationEvent|None = None


class STTIntegrationService(AvatarService):
    def __init__(self,
                 cache_folder: Path,
                 resample_to_rate: int|None = 16000,
                 enable_speaker_identification: bool = False,
                 emit_empty_recognitions: bool = False,
                 results_timeout_in_seconds: float = 5,
                 unfinished_timeout_in_seconds: float = 5*60,
                 ):
        self.cache_folder = Path(cache_folder)
        self.resample_to_rate = resample_to_rate
        self.enable_speaker_identification = enable_speaker_identification
        self.emit_empty_recognitions = emit_empty_recognitions
        self.results_timeout_in_seconds = results_timeout_in_seconds
        self.unfinished_timeout_in_seconds = unfinished_timeout_in_seconds
        self.recordings: dict[str, _Recording] = {}
        self.fixed_to_original: dict[str, str] = {}

    def requires_brainbox(self):
        return True

    @staticmethod
    def get_fixed_file_id(file_id: str) -> str:
        path = PurePosixPath(file_id)
        return str(path.with_name(path.stem + '.fixed.wav'))

    def _remove(self, file_id: str) -> _Recording|None:
        recording = self.recordings.pop(file_id, None)
        if recording is not None and recording.fixed_file_id is not None:
            self.fixed_to_original.pop(recording.fixed_file_id, None)
        return recording

    def _find(self, file_id: str) -> str|None:
        original = self.fixed_to_original.get(file_id, file_id)
        return original if original in self.recordings else None

    @message_handler
    def on_streaming_start(self, event: SoundStreamingStartEvent) -> None:
        self.recordings[event.file_id] = _Recording(datetime.now())

    @message_handler
    def on_streaming_end(self, event: SoundStreamingEndEvent) -> tuple[SoundEvent|TextEvent, ...]:
        if not event.success:
            self._remove(event.file_id)
            return ()
        recording = self.recordings.setdefault(event.file_id, _Recording(datetime.now()))
        fixed_file_id = self.get_fixed_file_id(event.file_id)
        fixed = _fix_wav_header((self.cache_folder/event.file_id).read_bytes())
        if self.resample_to_rate is not None:
            fixed = _resample_wav(fixed, self.resample_to_rate)
        (self.cache_folder/fixed_file_id).write_bytes(fixed)
        recording.finished_at = datetime.now()
        recording.fixed_file_id = fixed_file_id
        self.fixed_to_original[fixed_file_id] = event.file_id
        text_event = self._try_complete(event.file_id)
        if text_event is None:
            return (SoundEvent(fixed_file_id),)
        return (SoundEvent(fixed_file_id), text_event)

    @message_handler
    def on_recognition(self, event: RecognitionEvent) -> TextEvent|None:
        file_id = self._find(event.file_id)
        if file_id is None:
            return None
        self.recordings[file_id].recognition = event
        return self._try_complete(file_id)

    @message_handler
    def on_speaker_identification(self, event: SpeakerIdentificationEvent) -> TextEvent|None:
        file_id = self._find(event.file_id)
        if file_id is None:
            return None
        self.recordings[file_id].speaker = event
        return self._try_complete(file_id)

    def _try_complete(self, file_id: str) -> TextEvent|None:
        recording = self.recordings[file_id]
        if recording.finished_at is None:
            return None
        errors = [result.error for result in (recording.recognition, recording.speaker) if result is not None and result.error is not None]
        if len(errors) > 0:
            self._remove(file_id)
            raise ValueError(f"STT failed for {file_id}:\n" + '\n'.join(str(error) for error in errors))
        if recording.recognition is None:
            return None
        if self.enable_speaker_identification and recording.speaker is None:
            return None
        self._remove(file_id)

        recognition = recording.recognition.recognition
        if not isinstance(recognition, (str, Utterance)):
            raise ValueError(f"STT returned recognition of type {type(recognition)}, which is not expected:\n{recognition}")

        if not self.emit_empty_recognitions and isinstance(recognition, str) and recognition.strip() == '':
            logger.info(f"Nothing was recognized in {file_id}, no TextEvent is emitted")
            return None

        speaker = recording.speaker.speaker if recording.speaker is not None else None
        return TextEvent(recognition, speaker, recording.fixed_file_id)

    @message_handler
    def on_tick(self, event: TickEvent) -> None:
        timed_out = []
        for file_id, recording in list(self.recordings.items()):
            if recording.finished_at is not None:
                if (event.time - recording.finished_at).total_seconds() > self.results_timeout_in_seconds:
                    self._remove(file_id)
                    timed_out.append(file_id)
            elif (event.time - recording.started_at).total_seconds() > self.unfinished_timeout_in_seconds:
                self._remove(file_id)
        if len(timed_out) > 0:
            raise TimeoutError(f"STT results did not arrive in {self.results_timeout_in_seconds} seconds for {timed_out}")
