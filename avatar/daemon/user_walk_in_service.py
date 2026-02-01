from .common import AvatarService, message_handler, ImageEvent, IMessage, InitializationEvent
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
    file_id: str

@dataclass
class UserWalkInTrain(IMessage):
    file_id: str
    actual_user: str

class UserWalkInService(AvatarService):
    Event = UserWalkInEvent
    Train = UserWalkInTrain


    def __init__(self,
                 api: AvatarApi,
                 identification_strategy: IStrategy,
                 ):
        self.api = api
        self.identification_strategy = identification_strategy
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

    @message_handler.with_call(BrainBoxService.Command, BrainBoxService.Confirmation)
    def on_image_event(self, message: ImageEvent) -> UserWalkInEvent|None:
        user = self.identificator.analyze(message.file_id)
        if user is None:
            logger.info("User is not recognized")
            return None
        return UserWalkInEvent(user, message.file_id)


    @message_handler
    def train(self, message: UserWalkInTrain) -> None:
        self.identificator.add_sample(message.actual_user, message.file_id)
        self.identificator.initialize()


    def requires_brainbox(self):
        return True