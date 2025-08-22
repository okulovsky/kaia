from eaglesong import Listen
from avatar.daemon import OpenMicCommand, WhisperRecognitionSetup

class WhisperOpenMicListen(Listen):
    def __init__(self, whisper_prompt: str|None = None, whisper_language: str|None = None):
        super().__init__(
            WhisperRecognitionSetup(whisper_prompt, whisper_language),
            OpenMicCommand()
        )