import subprocess
import wave
import json
import os
from uuid import uuid4

from interface import IVosk, FileLike
from foundation_kaia.brainbox_utils import SingleModelStorage
from foundation_kaia.marshalling import FileLikeHandler, JSON
from vosk import KaldiRecognizer


class VoskService(IVosk):
    def __init__(self, storage: SingleModelStorage):
        self.storage = storage

    def transcribe(self, file: FileLike, model: str | None = None) -> JSON:
        model_obj = self.storage.get_model(model)
        fname = f'/resources/input_{uuid4()}.wav'
        try:
            FileLikeHandler.write(file, fname)
            try:
                wf = wave.open(fname, "rb")
            except Exception:
                fixed_fname = f'/resources/input_{uuid4()}.wav'
                subprocess.call(['ffmpeg', '-i', fname, fixed_fname])
                os.unlink(fname)
                fname = fixed_fname
                wf = wave.open(fname, "rb")

            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                raise ValueError("Audio file must be WAV format mono PCM.")
            rec = KaldiRecognizer(model_obj, wf.getframerate())
            rec.SetWords(True)
            results = []

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    part_result = json.loads(rec.Result())
                    results.append(part_result)

            part_result = json.loads(rec.FinalResult())
            results.append(part_result)

            return results
        finally:
            if os.path.isfile(fname):
                os.unlink(fname)

    def transcribe_to_array(self, file: FileLike, model: str | None = None) -> list[dict[str, JSON]]:
        result = self.transcribe(file, model)
        return [item for part in result for item in part['result']]

    def transcribe_to_string(self, file: FileLike, model: str | None = None) -> str:
        return ' '.join(z['word'] for z in self.transcribe_to_array(file, model))
