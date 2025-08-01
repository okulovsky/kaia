from typing import *
from .common import SoundConfirmation, TextInfo, SoundCommand, IMessage, message_handler, CommandConfirmationQueue, AvatarService
from abc import ABC, abstractmethod
from .brainbox_service import BrainBoxService
from brainbox import BrainBox
from dataclasses import dataclass

class VoiceoverServiceTaskFactory(ABC):
    @abstractmethod
    def create_task(self, s: str, info: TextInfo) -> BrainBox.ITask:
        pass

@dataclass
class VoiceoverServiceCommand(IMessage):
    text: tuple[str,...]
    settings: TextInfo

@dataclass
class PlayingElement:
    source_message_id: str
    sound_message_id: str

@dataclass
class VoiceoverServiceConfirmation(IMessage):
    pass

class VoiceoverService(AvatarService):
    Command = VoiceoverServiceCommand
    Confirmation = VoiceoverServiceConfirmation
    TaskFactory = VoiceoverServiceTaskFactory

    def __init__(self, task_factory: VoiceoverServiceTaskFactory):
        self.task_factory = task_factory
        self.queue = CommandConfirmationQueue[BrainBoxService.Command, BrainBoxService.Confirmation[SoundCommand]]()
        self.playing: PlayingElement|None = None

    def requires_brainbox(self):
        return True

    @message_handler
    def start_voiceover(self, input: VoiceoverServiceCommand) -> Tuple[BrainBoxService.Command,...]:
        output = []
        for line in input.text:
            task = self.task_factory.create_task(line, input.settings)
            message = BrainBoxService.Command(task, metadata=dict(source_message_id=input.envelop.id))
            output.append(message)
        self.queue.start_tracking(output)
        return tuple(output)

    def start_playing(self):
        while self.queue.get_processed_head_length() > 0:
            element = self.queue.deque()
            if element.confirmation.result is None:
                continue
            output = element.confirmation.result.with_new_envelop()
            self.playing = PlayingElement(
                element.command.metadata['source_message_id'],
                output.envelop.id
            )
            return (output,)
        return ()

    @message_handler
    def brainbox_finished(self, message: BrainBoxService.Confirmation[SoundCommand]):
        if not isinstance(message.result, SoundCommand):
            return
        self.queue.track(message)
        if self.playing is None:
            return self.start_playing()
        else:
            return ()

    @message_handler
    def play_finished(self, message: SoundConfirmation):
        if self.playing is None or not message.is_confirmation_of(self.playing.sound_message_id):
            return
        is_last = True
        for element in self.queue.queue:
            if element.command.metadata['source_message_id'] == self.playing.source_message_id:
                is_last = False
                break

        result = []
        if is_last:
            result.append(VoiceoverServiceConfirmation().as_confirmation_for(self.playing.sound_message_id))

        self.playing = None
        result.extend(self.start_playing())
        return result

    class MockTaskFactory(VoiceoverServiceTaskFactory):
        def create_task(self, s: str, settings: TextInfo) -> BrainBox.ITask:
            return 'TASK: '+s

    @staticmethod
    def brain_box_mock(task: BrainBox.Task):
        if not isinstance(task, str):
            raise ValueError("Expected string")
        if not task.startswith('TASK: '):
            raise ValueError("Expected string starting with TASK:")
        s = task[6:]
        return SoundCommand(
            'FILE: '+s,
            s
        )






