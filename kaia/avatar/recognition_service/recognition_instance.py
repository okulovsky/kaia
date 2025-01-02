from typing import Any
from enum import Enum
from brainbox import BrainBoxApi, BrainBoxTask, BrainBoxCombinedTask
from brainbox.deciders import RhasspyKaldi, Whisper, Resemblyzer, Collector
from ..state import State, MemoryItem
from dataclasses import dataclass
from ..world import World

class RecognitionSettings:
    class NLU(Enum):
        Rhasspy = 0
        Whisper = 1

    def __init__(self,
                 nlu: 'RecognitionSettings.NLU' = None,
                 whisper_prompt: None | str = None,
                 rhasspy_model: None | str = None,
                 ):
        if nlu is None:
            nlu = RecognitionSettings.NLU.Rhasspy
        self.nlu = nlu
        self.whisper_prompt = whisper_prompt
        self.rhasspy_model = rhasspy_model

@dataclass
class RecognitionData(MemoryItem):
    file_id: str
    settings: RecognitionSettings
    whisper_model: str
    resemblyzer_model_name: str|None

    used_rhasspy_model: str|None = None
    full_recognition: Any = None
    result: Any = None


    def _create_pack(self, base_task_name: str, base_task: BrainBoxTask, filename):
        base_tasks = [base_task]
        dependencies = {base_task_name: base_task.id}
        if self.resemblyzer_model_name is not None:
            resemblyzer_task = (
                BrainBoxTask
                .call(Resemblyzer)(file=filename, model=self.resemblyzer_model_name)
                .to_task(id = filename.split('.')[0]+'.resemblyzer')
            )
            base_tasks.append(resemblyzer_task)
            dependencies['resemblyzer'] = resemblyzer_task.id
        return BrainBoxCombinedTask(
            BrainBoxTask(decider=Collector.to_dict, dependencies=dependencies),
            tuple(base_tasks)
        )


    def run_rhasspy_recognition(self, state: State, brainbox_api: BrainBoxApi):
        self.used_rhasspy_model = self.settings.rhasspy_model
        if self.used_rhasspy_model is None:
            self.used_rhasspy_model = state.intents_packs[0].name
        task = (BrainBoxTask
                    .call(RhasspyKaldi)
                    .transcribe(file=self.file_id, model=self.used_rhasspy_model)
                    .to_task(id=self.file_id.split('.')[0] + '.rhasspy')
                )
        pack = self._create_pack('rhasspy', task, self.file_id)
        self.full_recognition = brainbox_api.execute(pack)
        fsticuffs = self.full_recognition['rhasspy']['fsticuffs']
        if len(fsticuffs) > 0:
            to_parse = fsticuffs[0]
            result = state.rhasspy_handlers[self.used_rhasspy_model].parse_json(to_parse)
            self.result = result
        else:
            self.result = None


    def run_whisper_recognition(self, brainbox_api: BrainBoxApi):
        task = (
            BrainBoxTask
            .call(Whisper)
            .transcribe(file=self.file_id, initial_prompt=self.settings.whisper_prompt, model=self.whisper_model)
            .to_task(id=self.file_id.split('.')[0] + '.whisper')
        )
        pack = self._create_pack('whisper', task, self.file_id)
        self.full_recognition = brainbox_api.execute(pack)
        self.result = self.full_recognition['whisper']


    def run(self, state: State, brainbox_api: BrainBoxApi):
        rhasspy = self.settings.nlu == self.settings.NLU.Rhasspy

        if rhasspy:
            self.run_rhasspy_recognition(state, brainbox_api)
        else:
            self.run_whisper_recognition(brainbox_api)

        if 'resemblyzer' in self.full_recognition:
            state.apply_change({World.user.field_name:self.full_recognition['resemblyzer']})

        state.add_memory(self)
