from typing import *
from kaia.kaia.audio_control import AudioControlAPI
from kaia.brainbox import BrainBoxApi, BrainBoxTask, BrainBoxTaskPack
from kaia.brainbox.deciders import Rhasspy, Whisper, Resemblyzer, Collector
from kaia.dub import Template
from kaia.dub.rhasspy_utils import RhasspyHandler
from kaia.kaia.gui import KaiaGuiApi, KaiaMessage
from kaia.avatar import AvatarAPI
from kaia.narrator import INarrator, World
from .audio_control_translator import AudioControlTranslator

class AudioControlHandler:
    def __init__(self,
                 audio_control_api: AudioControlAPI,
                 brain_box_api: BrainBoxApi,
                 kaia_gui_api: Optional[KaiaGuiApi],
                 intents_factory: Callable[[], Iterable[Template]],
                 resemblyzer_model_name: None|str = None,
                 avatar_api: None|AvatarAPI = None
                 ):
        self.audio_control_api = audio_control_api
        self.brain_box_api = brain_box_api
        self.kaia_gui_api = kaia_gui_api
        self.intents_factory = intents_factory
        self.resemblyzer_model_name = resemblyzer_model_name
        self.avatar_api = avatar_api

        self.intents = intents_factory()
        self.rhasspy_handler = RhasspyHandler(self.intents)


    def setup(self):
        self.intents = self.intents_factory()
        self.rhasspy_handler = RhasspyHandler(self.intents)

        if self.kaia_gui_api is not None:
            self.kaia_gui_api.add_message_fire_and_forget(KaiaMessage(True, 'Rhasspy is training'))

        self.brain_box_api.execute(self.create_train_rhasspy_task())

        if self.kaia_gui_api is not None:
            self.kaia_gui_api.add_message_fire_and_forget(KaiaMessage(True, 'Rhasspy has been trained'))


    def create_train_rhasspy_task(self):
        return BrainBoxTask(
            decider=Rhasspy.train,
            arguments=dict(intents=self.intents)
        )

    def _create_pack(self, base_task_name: str, base_task: BrainBoxTask, filename):
        base_tasks = [base_task]
        dependencies = {base_task_name: base_task.id}
        if self.resemblyzer_model_name is not None:
            resemblyzer_task = (
                BrainBoxTask
                .call(Resemblyzer)(file=filename)
                .to_task(
                    decider_parameters=self.resemblyzer_model_name,
                    id = filename.split('.')[0]+'.resemblyzer'
                ))
            base_tasks.append(resemblyzer_task)
            dependencies['resemblyzer'] = resemblyzer_task.id
        return BrainBoxTaskPack(
            BrainBoxTask(decider=Collector.to_dict, dependencies=dependencies),
            tuple(base_tasks)
        )

    def _postprocess_pack(self, result):
        if 'resemblyzer' in result and self.avatar_api is not None:
            self.avatar_api.state_change({World.user.field_name:result['resemblyzer']})


    def run_rhasspy_recognition(self, filename):
        task = BrainBoxTask.call(Rhasspy).recognize(file=filename).to_task(id=filename.split('.')[0] + '.rhasspy')
        pack = self._create_pack('rhasspy', task, filename)
        result = self.brain_box_api.execute(pack)
        self._postprocess_pack(result)
        result = self.rhasspy_handler.parse_json(result['rhasspy'])
        return result

    def run_whisper_recognition(self, filename, prompt=None):
        task = BrainBoxTask.call(Whisper).transcribe(file=filename, initial_prompt=prompt).to_task(id=filename.split('.')[0] + '.whisper')
        pack = self._create_pack('whisper', task, filename)
        result = self.brain_box_api.execute(pack)
        self._postprocess_pack(result)
        result = result['whisper']
        return result

    def create_translator(self, inner_function) -> 'AudioControlTranslator':
        return AudioControlTranslator(inner_function, self)
