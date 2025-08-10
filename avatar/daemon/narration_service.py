from .common import IMessage, State, message_handler, TimerEvent, InitializationEvent, AvatarService
from dataclasses import dataclass
import numpy as np
from datetime import datetime
from .image_service import NewImageCommand

@dataclass
class ChangeCharacterCommand(IMessage):
    character: str|None = None


@dataclass
class ChangeActivityCommand(IMessage):
    activity: str|None = None

@dataclass
class StateRequest(IMessage):
    pass




class NarrationService(AvatarService):
    ChangeCharacterCommand = ChangeCharacterCommand
    ChangeActivityCommand = ChangeActivityCommand
    StateRequest = StateRequest

    def __init__(self,
                 state: State,
                 characters: tuple[str, ...] | None = None,
                 activities: tuple[str, ...] | None = None,
                 welcome_command: IMessage | None = None,
                 time_between_updates_in_seconds: int | None = None,
                 randomize: bool = True,
                 ):
        self.state = state
        self.characters = characters
        self.activities = activities
        self.welcome_command = welcome_command
        self.time_between_images_in_seconds = time_between_updates_in_seconds
        self.randomize = randomize
        self.last_update_time: datetime = datetime.now()
        self.current_time: datetime = datetime.now()

    def _random_change(self, current, collection:tuple|None) -> str|None:
        if collection is None:
            return None
        others = [c for c in collection if c != current]
        if self.randomize:
            if len(others) == 0:
                return None
            idx = np.random.randint(0, len(others))
            if idx>=len(others):
                idx = len(others) - 1
            return others[idx]
        else:
            return others[0]

    @message_handler
    def change_character(self, message: ChangeCharacterCommand):
        if message.character is None:
            character = self._random_change(self.state.character, self.characters)
        else:
            character = message.character
        if character is not None:
            self.last_update_time = self.current_time
            self.state.character = character
            yield NewImageCommand()
            if self.welcome_command is not None:
                yield self.welcome_command.with_new_envelop()
            yield self.state.with_new_envelop().as_confirmation_for(message)

    @message_handler
    def change_activity(self, message: ChangeActivityCommand):
        if message.activity is None:
            activity = self._random_change(self.state.activity, self.activities)
        else:
            activity = message.activity
        if activity is not None:
            self.last_update_time = self.current_time
            self.state.activity = activity
            yield NewImageCommand()
            yield self.state.with_new_envelop().as_confirmation_for(message)

    @message_handler
    def on_tick(self, message: TimerEvent):
        self.current_time = message.time
        if (self.current_time - self.last_update_time).total_seconds() < self.time_between_images_in_seconds:
            return
        return tuple(self.change_activity(ChangeActivityCommand()))

    @message_handler
    def state_request(self, message: StateRequest):
        return self.state.with_new_envelop().as_confirmation_for(message)

    @message_handler
    def initialize(self, message: InitializationEvent):
        return self.change_character(ChangeCharacterCommand())

    def requires_brainbox(self):
        return False

