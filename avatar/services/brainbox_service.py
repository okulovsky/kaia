import traceback
from typing import Any, Type, Optional, Union, Callable, TypeVar, Generic
from ..messaging import IMessage, message_handler
from dataclasses import dataclass
from brainbox import BrainBox
from .common import AvatarService

@dataclass
class BrainBoxServiceCommand(IMessage):
    task: BrainBox.ITask
    metadata: Any = None

TResult = TypeVar("TResult")

@dataclass
class BrainBoxServiceConfirmation(IMessage, Generic[TResult]):
    result: TResult|None
    error: Any


class BrainBoxService(AvatarService):
    Command = BrainBoxServiceCommand
    Confirmation = BrainBoxServiceConfirmation

    def __init__(self, api: Union[BrainBox.Api, Callable]):
        if isinstance(api, BrainBox.Api):
            self.api_call = api.execute
        else:
            self.api_call = api

    def requires_brainbox(self):
        return True

    @message_handler
    def execute(self, input: BrainBoxServiceCommand):
        try:
            result = self.api_call(input.task)
            reply: IMessage = BrainBoxServiceConfirmation(result, None)
            return reply.as_confirmation_for(input)
        except Exception as ex:
            reply: IMessage = BrainBoxServiceConfirmation(None, ''.join(traceback.format_exception(ex)))
            return reply.as_confirmation_for(input)

