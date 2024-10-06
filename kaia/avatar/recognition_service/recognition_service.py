from kaia.brainbox import BrainBoxApi, BrainBoxTask, BrainBoxTaskPack
from kaia.brainbox.deciders import Resemblyzer, RhasspyKaldi
from ..state import State
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
            self.brainbox_api.execute(BrainBoxTask.call(RhasspyKaldi).train(intents_pack=pack))

    def speaker_train(self, state: State, media_library_path: Path):
        self.brainbox_api.execute(
            BrainBoxTask.call(Resemblyzer)
            .train_on_media_library(media_library_path=media_library_path)
            .to_task(decider_parameters=self.resemblyzer_model_name)
        )


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
        tasks = []
        dependencies = {}
        for i, item in enumerate(replace):
            fname = item.file_id
            task = (
                BrainBoxTask
                .call(Resemblyzer)
                .upload_dataset_file(split='train', speaker=actual_name, fname=fname)
                .to_task(decider_parameters=self.resemblyzer_model_name)
            )
            dependencies[f'*{i}'] = task.id
            tasks.append(task)
        train_task = BrainBoxTask.call(Resemblyzer).train().to_task(decider_parameters=self.resemblyzer_model_name)
        train_task.dependencies = dependencies
        pack = BrainBoxTaskPack(train_task, tuple(tasks))
        self.brainbox_api.execute(pack)
        return True








