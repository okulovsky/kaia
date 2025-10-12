from .common import AvatarService, message_handler, BackendIdleReport, ImageEvent, State, IMessage, InitializationEvent
from .common.vector_identificator import VectorIdentificator, IStrategy
from .brainbox_service import BrainBoxService
from brainbox import BrainBox
from brainbox.deciders import InsightFace
from ..server import AvatarApi
from dataclasses import dataclass
from loguru import logger

logger.disable(__name__)

@dataclass
class UserWalkInEvent(IMessage):
    user: str

class UserWalkInService(AvatarService):
    Event = UserWalkInEvent

    def __init__(self,
                 state: State,
                 api: AvatarApi,
                 identification_strategy: IStrategy,
                 idle_time_in_seconds = 60,
                 ):
        self.state = state
        self.api = api
        self.identification_strategy = identification_strategy
        self.idle_time_in_seconds = idle_time_in_seconds

        self.first_idle: BackendIdleReport|None = None
        self.identificator: VectorIdentificator|None = None

    @message_handler
    def on_initialize(self, message: InitializationEvent) -> None:
        self.identificator = VectorIdentificator(
            self.resources_folder,
            self.identification_strategy,
            self.image_to_vector,
            self.api.file_cache.open
        )
        self.identificator.initialize()


    def image_to_vector(self, file_id: str):
        task = BrainBox.Task.call(InsightFace).analyze(file_id)
        command = BrainBoxService.Command(task)
        result: BrainBoxService.Confirmation = self.client.run_synchronously(command, BrainBoxService.Confirmation)
        if len(result.result) != 1:
            return None
        return result.result[0]['embedding']


    @message_handler
    def on_backend_idle_report(self, message: BackendIdleReport):
        logger.info("BackendIdleReport received")
        if message.is_idle:
            if self.first_idle is None:
                logger.info('State in WalkIn set to Idle')
                self.first_idle = message
        else:
            logger.info('State in WalkIn set to Busy')
            self.first_idle = None

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def on_image_event(self, message: ImageEvent) -> UserWalkInEvent|None:
        if self.first_idle is None:
            logger.info('Image while busy')
            return None

        delta = (message.envelop.timestamp - self.first_idle.envelop.timestamp).total_seconds()
        if delta < self.idle_time_in_seconds:
            logger.info(f'Not enough idle time, {delta} seconds of {self.idle_time_in_seconds}')
            return None
        user = self.identificator.analyze(message.file_id)
        if user is None:
            logger.info("User is not recognized. Misconfigured service?")
            return None
        self.state.user = user
        yield UserWalkInEvent(user)



    def requires_brainbox(self):
        return True