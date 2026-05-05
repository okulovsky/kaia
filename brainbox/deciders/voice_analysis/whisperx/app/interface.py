from foundation_kaia.marshalling import service, FileLike
from foundation_kaia.brainbox_utils import BrainboxReportItem, brainbox_websocket
from typing import Iterable


@service
class WhisperXInterface:
    @brainbox_websocket
    def execute(self, audio: FileLike, hf_token: str, language: str = 'en', model: str = 'base') -> Iterable[BrainboxReportItem[str]]:
        """Transcribes and word-aligns audio using WhisperX, streaming progress updates."""
        ...
