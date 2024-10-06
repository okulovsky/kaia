from dataclasses import dataclass
from .text_processor import TextLike, TextProcessor
from .task_generator import IDubTaskGenerator
from kaia.eaglesong.core import Audio
from kaia.brainbox import BrainBoxApi
from ..media_library_manager import MediaLibraryManager
from .paraphrase_service import ParaphraseService
from ..state import State

@dataclass
class DubbingServiceOutput:
    full_text: str
    jobs: tuple[str,...]


class DubbingService:
    def __init__(self,
                 task_generator: IDubTaskGenerator,
                 api: BrainBoxApi,
                 manager: None|MediaLibraryManager = None
    ):
        self.api = api
        self.task_generator = task_generator
        self.text_processor = TextProcessor()
        self.paraphraser = None if manager is None else ParaphraseService(manager)

    def stream_dub(self, text: TextLike, state: dict[str, str]):
        data = self.text_processor.process(text)
        jobs = []
        for chunk in data.chunks:
            task = self.task_generator.generate_task(chunk, state)
            self.api.add(task)
            jobs.append(task.id)
        return DubbingServiceOutput(data.full_text, tuple(jobs))

    def legacy_one_audio_dub(self, text: TextLike, state: dict[str, str]):
        data = self.text_processor.process(text)
        task = self.task_generator.generate_task(data.full_text, state)
        result = self.api.execute(task)
        result = self.task_generator.unpack_result(self.api, result)
        return Audio(result, data.full_text)

    def dub(self, state: State, text: TextLike):
        if self.paraphraser is not None:
            text = self.paraphraser.paraphrase(text, state.get_state())
        return self.stream_dub(text, state.get_state())


    def get_result(self, job_id: str):
        result = self.api.join(job_id)
        audio = self.task_generator.unpack_result(self.api, result)
        return Audio(audio)




