from typing import *
from abc import abstractmethod, ABC
from brainbox import BrainBox
from brainbox.deciders import Collector


class VoiceCloner(ABC):
    @abstractmethod
    def get_voice_cloner_key(self):
        pass

    @abstractmethod
    def create_voiceover_task_and_tags(self, text: str) -> tuple[BrainBox.ITask, dict]:
        pass

    @abstractmethod
    def create_training_tasks(self) -> dict[str,BrainBox.ITask]:
        pass

    @property
    def model_prefix(self) -> str|None:
        if not hasattr(self, '_model_prefix'):
            return None
        return self._model_prefix

    @model_prefix.setter
    def model_prefix(self, value: str):
        self._model_prefix = value

    def create_model_name(self, *parts):
        model_name = '_'.join(p for p in parts if p is not None)
        if self.model_prefix is not None:
            model_name = self.model_prefix + '_' + model_name
        return model_name

    def tags(self, text, **kwargs):
        result = dict(
            voice_cloner=type(self).__name__,
            case_key = self.get_voice_cloner_key(),
            text = text,
            model_prefix = self.model_prefix,
        )
        for k,v in kwargs.items():
            result[k] = v
        return result

    @staticmethod
    def joint_training_task(upsamplers: Iterable['VoiceCloner']) -> BrainBox.ITask:
        result = {}
        for upsampler in upsamplers:
            for model_name, task in upsampler.create_training_tasks().items():
                key = (type(upsampler).__name__, model_name)
                if key not in result:
                    result[key] = task
        builder = Collector.TaskBuilder()
        for (upsampler, model_name), task in result.items():
            builder.append(task, dict(upsampler=upsampler, model_name=model_name))
        return builder.to_collector_pack('to_array')




