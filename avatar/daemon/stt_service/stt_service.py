from .stt import IRecognitionSetup, RecognitionContext, STTCommand, STTConfirmation, RhasspyRecognitionSetup
from .rhasspy_training import IntentsPack, RhasspyHandler
from ..common import IMessage, message_handler, AvatarService
from ..brainbox_service import BrainBoxService
from dataclasses import dataclass
from brainbox import BrainBox
import jsonpickle


@dataclass
class STTRhasspyTrainingCommand(IMessage):
    intent_packs: list[IntentsPack]


class STTService(AvatarService):
    Command = STTCommand
    Confirmation = STTConfirmation
    RhasspyTrainingCommand = STTRhasspyTrainingCommand

    def __init__(self,
                 default_setup: IRecognitionSetup,
                 ):
        self.default_setup = default_setup
        self.requested_setup: IRecognitionSetup|None = None
        self.last_recognitions = []
        self.handlers: dict[str, RhasspyHandler] = {}

    def requires_brainbox(self):
        return True

    @message_handler
    def setup(self, message: IRecognitionSetup) -> None:
        self.requested_setup = message

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def recognize(self, sound: STTCommand) -> STTConfirmation:
        if sound.setup is not None:
            setup = sound.setup
        else:
            setup = self.default_setup
            if self.requested_setup is not None:
                setup = self.requested_setup
                self.requested_setup = None

        context = RecognitionContext(sound, self.handlers)
        recognition_task = setup.create_task(context)
        bb_command = BrainBoxService.Command(recognition_task).as_reply_to(sound)
        bb_result = self.client.run_synchronously(bb_command, BrainBoxService.Confirmation)
        result: STTConfirmation = bb_result.result
        if result is None:
            raise ValueError(f"Expected result, error\n{bb_result.error}")
        return result.as_confirmation_for(sound).as_reply_to(bb_result)



    @message_handler
    def train_rhasspy(self, message: STTRhasspyTrainingCommand) -> BrainBoxService.Command:
        for pack in message.intent_packs:
            self.handlers[pack.name] = RhasspyHandler(pack.templates)
        task = RhasspyRecognitionSetup.create_training_task(message.intent_packs)
        return (
            BrainBoxService
            .Command(task)
            .as_propagation_confirmation_to(message)
        )

    @staticmethod
    def brain_box_mock(task: BrainBox.ITask):
        jobs = task.create_jobs()
        if jobs[-1].decider=='EmptyDecider': #It means training
            return 'OK'
        if len(jobs) != 1:
            raise ValueError("Must be either multi-job task for training, or a single-job task for recognition")
        job = jobs[0]
        return jsonpickle.loads(job.arguments['file'])[job.decider]

