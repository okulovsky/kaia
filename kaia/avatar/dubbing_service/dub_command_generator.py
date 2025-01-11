from abc import ABC, abstractmethod
from brainbox import BrainBoxTask, BrainBoxCommand, FilePostprocessor, File, BrainBoxExtendedTask
from brainbox.deciders import FakeFile, OpenTTS
from ..world import World
from dataclasses import dataclass


class IDubCommandGenerator(ABC):
    @abstractmethod
    def generate_command(self, text: str, state: dict[str, str]) -> BrainBoxCommand[File]:
        pass



class TestTaskGenerator(IDubCommandGenerator):
    def generate_command(self, text: str, state: dict[str, str]) -> BrainBoxCommand[File]:
        character = state[World.character.field_name]
        if not character.startswith('character_'):
            raise ValueError(f"Unexpected character name {character}")
        voice = character.replace('character_', 'voice_')
        task = BrainBoxTask.call(FakeFile).__call__(dict(voice=voice,text=text))
        pack = BrainBoxExtendedTask(task, postprocessor=FilePostprocessor())
        return BrainBoxCommand(pack)

@dataclass
class DubbingMetadata:
    text: str
    speaker: str
    voice: str


class OpenTTSTaskGenerator(IDubCommandGenerator):
    def __init__(self, voices: dict[str, str]):
        self.voices = voices

    def generate_command(self, text: str, state:dict[str, str]) -> BrainBoxCommand[File]:
        voice_name = state[World.character.field_name]
        voice = self.voices[voice_name]
        task = BrainBoxTask.call(OpenTTS)(voice='coqui-tts:en_vctk', lang='en', speakerId=voice, text=text)
        pack = BrainBoxExtendedTask(task, postprocessor=FilePostprocessor(metadata=DubbingMetadata(text, voice_name, voice)))
        return BrainBoxCommand(pack)

