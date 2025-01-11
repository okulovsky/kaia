from dataclasses import dataclass
from .text_processor import TextLike, TextProcessor
from .dub_command_generator import IDubCommandGenerator
from brainbox import BrainBoxApi, BrainBoxCommand, File
from ..media_library_manager import MediaLibraryManager
from .paraphrase_service import ParaphraseService, ParaphraseServiceSettings
from ..state import State

@dataclass
class DubbingServiceOutput:
    full_text: str
    jobs: tuple[str,...]




class DubbingService:
    def __init__(self,
                 task_generator: IDubCommandGenerator,
                 api: BrainBoxApi,
                 paraphrase_settings: ParaphraseServiceSettings|None = None
    ):
        self.api = api
        self.task_generator = task_generator
        self.text_processor = TextProcessor()
        self.paraphraser = None if paraphrase_settings is None else ParaphraseService(paraphrase_settings)
        self._id_to_command: dict[str, BrainBoxCommand[File]] = {}

    def _stream_dub(self, text: TextLike, state: dict[str, str]):
        data = self.text_processor.process(text)
        jobs = []
        for chunk in data.chunks:
            command = self.task_generator.generate_command(chunk, state)
            command.add(self.api)
            id = command.task.get_resulting_id()
            jobs.append(id)
            self._id_to_command[id] = command
        return DubbingServiceOutput(data.full_text, tuple(jobs))

    def dub(self, state: State, text: TextLike):
        if self.paraphraser is not None:
            text = self.paraphraser.paraphrase(text, state.get_state())
        return self._stream_dub(text, state.get_state())


    def get_result(self, job_id: str):
        result = self._id_to_command[job_id].join(self.api)
        return result




