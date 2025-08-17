import jsonpickle

from brainbox import BrainBox, CombinedPrerequisite, IPrerequisite, BrainBoxApi
from brainbox.deciders import Resemblyzer
from .common import SoundEvent, IMessage, message_handler, IService, State, AvatarService
from .brainbox_service import BrainBoxService
from dataclasses import dataclass
from typing import cast

@dataclass
class SpeakerIdentificationTrain(IMessage):
    true_speaker: str

@dataclass
class SpeakerIdentificationTrainConfirmation(IMessage):
    admit_errors: bool

@dataclass
class SpeakerIdentificationTrainingPrerequisite(IPrerequisite):
    model: str
    true_speaker: str
    file: str

    def execute(self, api: BrainBoxApi):
        Resemblyzer.upload_dataset_file(
            self.model,
            'train',
            self.true_speaker,
            api.open_file(self.file)
        ).execute(api)


class SpeakerIdentificationService(AvatarService):
    Train = SpeakerIdentificationTrain
    TrainConfirmation = SpeakerIdentificationTrainConfirmation


    def __init__(self, state: State, resemblyzer_model: str):
        self.state = state
        self.resemblyzer_model = resemblyzer_model
        self.buffer: list[tuple[SoundEvent,str]] = []



    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def analyze(self, message: SoundEvent) -> None:
        command = BrainBoxService.Command(
            BrainBox.Task
            .call(Resemblyzer).distances(file=message.file_id, model=self.resemblyzer_model)
            .to_task(id=message.file_id.split('.')[0] + '.resemblyzer'),
            dict(source_message_id=message.envelop.id)
        )
        result = self.client.run_synchronously(command, BrainBoxService.Confirmation)
        speaker = result.result
        if result is not None:
            self.state.user = speaker
            self.buffer.append((message,speaker))
            self.buffer = self.buffer[-2:]



    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def train(self, message: SpeakerIdentificationTrain) -> SpeakerIdentificationTrainConfirmation:
        prereqs = []
        for event, speaker in self.buffer:
            if speaker == message.true_speaker:
                continue
            prereqs.append(SpeakerIdentificationTrainingPrerequisite(self.resemblyzer_model, message.true_speaker, event.file_id))
        if len(prereqs) == 0:
            return SpeakerIdentificationTrainConfirmation(False)
        self.state.user = message.true_speaker
        train_task = BrainBox.Task.call(Resemblyzer).train(self.resemblyzer_model)
        pack = BrainBox.ExtendedTask(train_task, prerequisite=CombinedPrerequisite(prereqs))
        self.client.run_synchronously(BrainBoxService.Command(pack), BrainBoxService.Confirmation)
        return SpeakerIdentificationTrainConfirmation(True)

    @staticmethod
    def brain_box_mock(task: BrainBox.ITask):
        jobs = task.create_jobs()
        if len(jobs)!=1:
            raise ValueError("Expected 1 job")
        job = jobs[0]
        if job.method == 'train':
            return 'OK'
        return job.arguments['file'].split(' ')[0]

    def requires_brainbox(self):
        return True





    