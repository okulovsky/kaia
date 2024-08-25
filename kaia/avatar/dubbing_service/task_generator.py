from abc import ABC, abstractmethod
from kaia.brainbox.core import BrainBoxTask, DownloadingPostprocessor, BrainBoxApi
from kaia.infra import FileIO
from kaia.narrator import World


class IDubTaskGenerator(ABC):
    @abstractmethod
    def generate_task(self, text: str, state: dict[str, str]) -> BrainBoxTask:
        pass

    @abstractmethod
    def unpack_result(self, api: BrainBoxApi, result) -> bytes:
        pass


class TestTaskGenerator(IDubTaskGenerator):
    def generate_task(self, text: str, state: dict[str, str]) -> BrainBoxTask:
        character = state[World.character.field_name]
        if not character.startswith('character_'):
            raise ValueError(f"Unexpected character name {character}")
        voice = character.replace('character_', 'voice_')
        return BrainBoxTask(decider='fake_tts', arguments=dict(text=text, voice=voice))

    def unpack_result(self, api, result) -> bytes:
        return FileIO.read_json(api.download(result[0]))



class OpenTTSTaskGenerator(IDubTaskGenerator):
    def __init__(self, voices: dict[str, str]):
        self.voices = voices
        self.postprocessor = DownloadingPostprocessor(opener=FileIO.read_bytes)

    def generate_task(self, text: str, state:dict[str, str]) -> BrainBoxTask:
        voice = self.voices[state[World.character.field_name]]
        return BrainBoxTask(
                id=BrainBoxTask.safe_id(),
                decider='OpenTTS',
                arguments=dict(voice='coqui-tts:en_vctk', lang='en', speakerId=voice, text=text)
            )

    def unpack_result(self, api: BrainBoxApi, result) -> bytes:
        return self.postprocessor.postprocess(result, api)