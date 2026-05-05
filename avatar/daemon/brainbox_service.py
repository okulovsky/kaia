import traceback
from typing import Any, TypeVar, Generic
from ..messaging import IMessage, message_handler
from dataclasses import dataclass
from brainbox import BrainBox
from .common import AvatarService

@dataclass
class BrainBoxServiceCommand(IMessage):
    task: BrainBox.Task
    metadata: Any = None

TResult = TypeVar("TResult")

@dataclass
class BrainBoxServiceConfirmation(IMessage, Generic[TResult]):
    result: TResult|None
    error: Any



class BrainBoxService(AvatarService):
    Command = BrainBoxServiceCommand
    Confirmation = BrainBoxServiceConfirmation

    def __init__(self,
                 api: BrainBox.Api,
                 ):
        self.api = api

    def requires_brainbox(self):
        return True

    @message_handler
    def execute(self, input: BrainBoxServiceCommand) -> BrainBoxServiceConfirmation:
        try:
            result = self.api.execute(input.task)
            reply: IMessage = BrainBoxServiceConfirmation(result, None)
            return reply.as_confirmation_for(input)
        except Exception as ex:
            reply: IMessage = BrainBoxServiceConfirmation(None, ''.join(traceback.format_exception(ex)))
            return reply.as_confirmation_for(input)

