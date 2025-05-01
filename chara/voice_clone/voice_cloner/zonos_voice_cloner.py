from brainbox import BrainBox
from brainbox.deciders import Zonos
from .voice_cloner import VoiceCloner
from yo_fluq import *
from dataclasses import dataclass
from .character import Character
from ...tools import Language, LanguageToDecider

@dataclass
class ZonosVoiceCloner(VoiceCloner):
    character: Character
    language: Language
    emotion: Any = None
    speaking_rate: float|None = None

    def get_voice_cloner_key(self):
        return self.character.name+'/'+str(self.emotion)+'/'+str(self.speaking_rate)

    def create_voiceover_task_and_tags(self, text: str) -> tuple[BrainBox.ITask, dict]:
        task = BrainBox.Task.call(Zonos).voiceover(
            text,
            self.create_model_name(self.character.name),
            LanguageToDecider.map(self.language, Zonos),
            emotion=self.emotion,
            speaking_rate=self.speaking_rate
        )
        tags = self.tags(
            text,
            character = self.character.name,
            language = self.language.name,
            emotion = [float(z) for z in self.emotion] if self.emotion is not None else None,
            speaking_rate = self.speaking_rate
        )
        return task, tags

    def create_training_tasks(self) -> dict[str,BrainBox.ITask]:
        model_name = self.create_model_name(self.character.name)
        task = BrainBox.Task.call(Zonos).train(model_name, self.character.get_voice_samples())
        return {model_name:task}



