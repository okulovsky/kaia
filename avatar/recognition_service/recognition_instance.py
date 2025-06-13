from brainbox import BrainBoxApi, BrainBoxTask, BrainBoxCombinedTask
from brainbox.deciders import RhasspyKaldi, Whisper, Resemblyzer, Collector, Vosk
from ..state import State, MemoryItem, WorldFields
from dataclasses import dataclass
from yo_fluq import *
from eaglesong.templates import TemplateBase, AStarParser

class RecognitionSettings:
    class NLU(Enum):
        Rhasspy = 0
        Whisper = 1
        Vosk = 2

    def __init__(self,
                 nlu: 'RecognitionSettings.NLU' = None,
                 whisper_prompt: None | str = None,
                 rhasspy_model: None | str = None,
                 vosk_model: None | str = None,
                 whisper_language: None| str = None,
                 free_speech_recognition_template: None|TemplateBase = None
                 ):
        if nlu is None:
            nlu = RecognitionSettings.NLU.Rhasspy
        self.nlu = nlu
        self.whisper_prompt = whisper_prompt
        self.rhasspy_model = rhasspy_model
        self.vosk_model = vosk_model
        self.whisper_language = whisper_language
        self.free_speech_recognition_template = free_speech_recognition_template


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
                .call(Resemblyzer).distances(file=filename, model=self.resemblyzer_model_name)
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
        kaldi_output = self.full_recognition['rhasspy']
        self.result = state.rhasspy_handlers[self.used_rhasspy_model].parse_kaldi_output(kaldi_output)

    def check_free_speech(self, s: str):
        if self.settings.free_speech_recognition_template is None:
            return s
        parser = AStarParser(self.settings.free_speech_recognition_template.dub)
        result = parser.parse(s)
        return self.settings.free_speech_recognition_template(result)


    def run_whisper_recognition(self, brainbox_api: BrainBoxApi):
        language_argument = None
        if self.settings.whisper_language is not None:
            language_argument = dict(language = self.settings.whisper_language)
        task = (
            BrainBoxTask
            .call(Whisper)
            .transcribe(
                file=self.file_id,
                initial_prompt=self.settings.whisper_prompt,
                model=self.whisper_model,
                parameters=language_argument
            )
            .to_task(id=self.file_id.split('.')[0] + '.whisper')
        )
        pack = self._create_pack('whisper', task, self.file_id)
        self.full_recognition = brainbox_api.execute(pack)
        self.result = self.check_free_speech(self.full_recognition['whisper'])

    def run_vosk_recognition(self, brainbox_api: BrainBoxApi):
        task = (
            BrainBoxTask
            .call(Vosk)
            .transcribe_to_string(file = self.file_id, model_name=self.settings.vosk_model)
            .to_task(id=self.file_id.split('.')[0]+'.vosk')
        )
        pack = self._create_pack('vosk', task, self.file_id)
        self.full_recognition = brainbox_api.execute(pack)
        self.result = self.check_free_speech(self.full_recognition['vosk'])

    def _fix_recognition(self):
        return Query.en(self.full_recognition['resemblyzer']).argmax(lambda z: z['score'])['speaker']

    def run(self, state: State, brainbox_api: BrainBoxApi):
        if self.settings.nlu == self.settings.NLU.Rhasspy:
            self.run_rhasspy_recognition(state, brainbox_api)
        elif self.settings.nlu == self.settings.NLU.Vosk:
            self.run_vosk_recognition(brainbox_api)
        else:
            self.run_whisper_recognition(brainbox_api)

        if 'resemblyzer' in self.full_recognition:
            state.apply_change({WorldFields.user:self._fix_recognition()})

        state.add_memory(self)
