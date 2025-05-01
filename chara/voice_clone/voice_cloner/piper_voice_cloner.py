from brainbox import BrainBox
from brainbox.deciders import Piper, OpenVoice, Collector
from .voice_cloner import VoiceCloner
from .character import Character
from ...tools import Language, LanguageToDecider
from yo_fluq import *
from dataclasses import dataclass

@dataclass
class PiperVoiceCloner(VoiceCloner):
    character: Character
    language: Language
    
    def _create_piper_task(self, text: str):
        return BrainBox.Task.call(Piper).voiceover(text, LanguageToDecider.map(self.language, Piper))

    def _create_training_from(self):
        builder = Collector.TaskBuilder()
        for text in self.language.sample_text:
            builder.append(
                self._create_piper_task(text),
                {}
            )
        piper_task = builder.to_collector_pack('to_result_array')
        model_name = self.create_model_name('from', self.language.name)
        train_task = BrainBox.Task.call(OpenVoice).train(
            model_name,
            piper_task
        )
        result = BrainBox.CombinedTask(
            train_task,
            (piper_task, )
        )
        return model_name, result

    def create_training_tasks(self) -> dict[str,BrainBox.ITask]:
        to_model_name = self.create_model_name('to', self.character.name)
        to_task = BrainBox.Task.call(OpenVoice).train(
            to_model_name,
            self.character.get_voice_samples()
        )
        from_model_name, from_task = self._create_training_from()
        return {
            to_model_name: to_task,
            from_model_name: from_task
        }

    def get_voice_cloner_key(self):
        return self.character.name

    def create_voiceover_task_and_tags(self, text: str) -> tuple[BrainBox.ITask, dict]:
        piper = self._create_piper_task(text)
        open_voice = BrainBox.Task.call(OpenVoice).generate(
            piper,
            self.create_model_name('to', self.character.name),
            self.create_model_name('from', self.language.name)
        )
        task = BrainBox.CombinedTask(
            open_voice,
            (piper, )
        )
        tags = self.tags(
            text,
            character = self.character.name,
            language = self.language.name
        )
        return task, tags
