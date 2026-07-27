from typing import *
from ..common import IMessage, State, message_handler, TickEvent, InitializationEvent, AvatarService, TextCommand
from dataclasses import dataclass
from datetime import datetime
from ..image_service import PhotoAlbumCommand
from .narrator import INarrator

@dataclass
class ChangeCharacterCommand(IMessage):
    character: str|None = None


@dataclass
class ChangeActivityCommand(IMessage):
    pass


@dataclass
class StateRequest(IMessage):
    pass


@dataclass
class LanguageRequest(IMessage):
    language: str


class NarrationService(AvatarService):
    ChangeCharacterCommand = ChangeCharacterCommand
    ChangeActivityCommand = ChangeActivityCommand
    StateRequest = StateRequest
    LanguageRequest = LanguageRequest

    def __init__(self,
                 state: State,
                 narrator: INarrator,
                 welcome_command: TextCommand | None = None,
                 time_between_updates_in_seconds: int | None = None,
                 ):
        self.state = state
        self.narrator = narrator
        self.welcome_command = welcome_command
        self.time_between_images_in_seconds = time_between_updates_in_seconds
        self.last_update_time: datetime = datetime.now()
        self.current_time: datetime = datetime.now()

    @message_handler
    def change_language(self, message: LanguageRequest) -> State:
        self.state.language = message.language
        return self.state.with_new_envelop().as_confirmation_for(message)

    @message_handler
    def change_character(self, message: ChangeCharacterCommand) -> Iterable[Union[PhotoAlbumCommand, State, TextCommand]]:
        character = self.narrator.update_character(self.state, message.character)
        if character is None:
            return
        self.last_update_time = self.current_time
        records = self.narrator.update_activity(self.state)
        yield PhotoAlbumCommand(records)
        if self.welcome_command is not None:
            yield self.welcome_command.with_new_envelop()
        print(self.state)
        yield self.state.with_new_envelop().as_confirmation_for(message)

    @message_handler
    def change_activity(self, message: ChangeActivityCommand) -> Iterable[Union[PhotoAlbumCommand, State]]:
        self.last_update_time = self.current_time
        records = self.narrator.update_activity(self.state)
        yield PhotoAlbumCommand(records)
        yield self.state.with_new_envelop().as_confirmation_for(message)

    @message_handler
    def on_tick(self, message: TickEvent) -> Iterable[Union[PhotoAlbumCommand, State]]:
        self.current_time = message.time
        if (self.current_time - self.last_update_time).total_seconds() < self.time_between_images_in_seconds:
            return
        self.last_update_time = self.current_time
        records = self.narrator.regular_update(self.state)
        yield PhotoAlbumCommand(records)
        yield self.state.with_new_envelop().as_confirmation_for(message)

    @message_handler
    def state_request(self, message: StateRequest) -> State:
        return self.state.with_new_envelop().as_confirmation_for(message)

    @message_handler
    def initialize(self, message: InitializationEvent) -> Iterable[Union[PhotoAlbumCommand, State, TextCommand]]:
        self.last_update_time = self.current_time
        records = self.narrator.initialize(self.state)
        yield PhotoAlbumCommand(records)
        if self.welcome_command is not None:
            yield self.welcome_command.with_new_envelop()
        print(self.state)
        yield self.state.with_new_envelop().as_confirmation_for(message)

    def requires_brainbox(self):
        return False
