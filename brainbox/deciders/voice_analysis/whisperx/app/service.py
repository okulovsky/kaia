import json
import uuid
from pathlib import Path
from typing import Iterable

from foundation_kaia.marshalling import FileLike, FileLikeHandler
from foundation_kaia.brainbox_utils import BrainboxReportItem, LongBrainboxProcess, logger
from interface import WhisperXInterface


class WhisperXProcess(LongBrainboxProcess[str]):
    def __init__(self, audio_path: Path, hf_token: str, language: str, model: str):
        self.audio_path = audio_path
        self.hf_token = hf_token
        self.language = language
        self.model = model

    def execute(self) -> str:
        import torch
        import whisperx

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.info(f"Loading model '{self.model}' on device '{device}'")
            whisperx_model = whisperx.load_model(
                self.model, device=device, compute_type='float32', download_root='/resources/models/'
            )
            model_a, metadata = whisperx.load_align_model(language_code=self.language, device=device)
            diarize_model = whisperx.diarize.DiarizationPipeline(
                use_auth_token=self.hf_token, device=device
            )

            logger.info("Transcribing audio")
            audio = whisperx.load_audio(str(self.audio_path))
            result = whisperx_model.transcribe(audio, language=self.language, batch_size=16)
            result = whisperx.align(
                result["segments"], model_a, metadata, audio, device, return_char_alignments=False
            )
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            for segment in result["segments"]:
                segment.pop('words')

            return json.dumps({"file": self.audio_path.name, "segments": result["segments"]})
        finally:
            self.audio_path.unlink(missing_ok=True)


class WhisperXService(WhisperXInterface):
    def execute(self, audio: FileLike, hf_token: str, language: str = 'en', model: str = 'base') -> Iterable[BrainboxReportItem[str]]:
        audio_path = Path(f'/resources/tmp_{uuid.uuid4()}.mp4')
        FileLikeHandler.write(audio, audio_path)
        process = WhisperXProcess(audio_path, hf_token, language, model)
        return process.start_process('/resources/log.html')
