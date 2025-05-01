from brainbox import BrainBox
from brainbox.deciders import CoquiTTS, EmptyTask
from .voice_cloner import VoiceCloner
from .character import Character
from ...tools import Language, LanguageToDecider
from dataclasses import dataclass
from yo_fluq import *

@dataclass
class CoquiVoiceCloner(VoiceCloner):
    character: Character
    language: Language

    def get_voice_cloner_key(self):
        return self.character.name

    def create_voiceover_task_and_tags(self, text: str) -> tuple[BrainBox.ITask, dict]:
        task = BrainBox.Task.call(CoquiTTS).voice_clone(
            text,
            model='tts_models/multilingual/multi-dataset/xtts_v2',
            voice=self.create_model_name(self.character.name),
            language=LanguageToDecider.map(self.language, CoquiTTS)
        )
        tags = self.tags(
            text,
            character = self.character.name,
            language = self.language.name
        )
        return task, tags

    def create_training_tasks(self) -> dict[str,BrainBox.ITask]:
        model_name = self.create_model_name(self.character.name)
        task = BrainBox.ExtendedTask(
            BrainBox.Task.call(EmptyTask)(),
            prerequisite=CoquiTTS.upload_voice(
                model_name,
                *self.character.get_voice_samples()
            )
        )
        return {model_name:task}


