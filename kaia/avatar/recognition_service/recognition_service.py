from brainbox import BrainBoxApi, BrainBoxTask, BrainBoxExtendedTask, CombinedPrerequisite
from brainbox.deciders import Resemblyzer, RhasspyKaldi
from ..state import State, RhasspyHandler
from .recognition_instance import RecognitionSettings, RecognitionData
from pathlib import Path



class RecognitionService:
    def __init__(self,
                 brainbox_api: BrainBoxApi,
                 resemblyzer_model_name: str,
                 whisper_model: str
                 ):
        self.brainbox_api = brainbox_api
        self.resemblyzer_model_name = resemblyzer_model_name
        self.whisper_model = whisper_model

    def transcribe(self, state: State, file: str, recognition_settings: RecognitionSettings):
        data = RecognitionData(
            file_id=file,
            settings = recognition_settings,
            whisper_model = self.whisper_model,
            resemblyzer_model_name = self.resemblyzer_model_name,
        )
        data.run(state, self.brainbox_api)
        return data.result

    def train(self, state: State):
        for pack in state.intents_packs:
            sentences = RhasspyHandler(pack.templates).ini_file
            self.brainbox_api.execute(BrainBoxTask.call(RhasspyKaldi).train(pack.name, pack.language, sentences, pack.custom_words))


    def speaker_train(self, media_library_path: Path):
        prereq = Resemblyzer.upload_dataset(self.resemblyzer_model_name, media_library_path)
        task = BrainBoxTask.call(Resemblyzer).train(self.resemblyzer_model_name)
        pack = BrainBoxExtendedTask(task, prerequisite=prereq)
        self.brainbox_api.execute(pack)


    def correct_speaker_recognition(self, state: State, actual_name: str) -> bool:
        key = 'resemblyzer'
        replace: list[RecognitionData] = (
            state
            .iterate_memory_reversed()
            .where(lambda z: isinstance(z, RecognitionData))
            .take(2)
            .where(lambda z: key in z.full_recognition)
            .where(lambda z: z.full_recognition[key] != actual_name)
            .to_list()
        )
        if len(replace) == 0:
            return False
        prereqs = []
        for i, item in enumerate(replace):
            fname = item.file_id
            prereqs.append(
                Resemblyzer.upload_dataset_file(
                    self.resemblyzer_model_name,
                    'train',
                    actual_name,
                    self.brainbox_api.open_file(fname)
                )
            )
        train_task = BrainBoxTask.call(Resemblyzer).train(self.resemblyzer_model_name)
        pack  = BrainBoxExtendedTask(train_task, prerequisite=CombinedPrerequisite(prereqs))
        self.brainbox_api.execute(pack)
        return True








