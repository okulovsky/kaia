from typing import *
from .common import Confirmation, SoundConfirmation, TextInfo, SoundCommand, IMessage, message_handler, CommandConfirmationQueue, AvatarService
from abc import ABC, abstractmethod
from .brainbox_service import BrainBoxService
from brainbox import BrainBox, IPostprocessor
from dataclasses import dataclass

class TTSTaskFactory(ABC):
    @abstractmethod
    def create_task(self, s: str, info: TextInfo) -> BrainBox.ITask:
        pass

@dataclass
class TTSCommand(IMessage):
    text: tuple[str,...]
    settings: TextInfo

@dataclass
class PlayingElement:
    source_message_id: str
    sound_message_id: str

class TTSPostprocessor(IPostprocessor):
    def __init__(self, text: str):
        self.text = text

    def postprocess(self, result, api):
        return SoundCommand(result, self.text)



class TTSService(AvatarService):
    Command = TTSCommand
    TaskFactory = TTSTaskFactory

    def __init__(self, task_factory: TTSTaskFactory):
        self.task_factory = task_factory
        self.queue = CommandConfirmationQueue[BrainBoxService.Command, BrainBoxService.Confirmation[SoundCommand]]()
        self.playing: PlayingElement|None = None

    def requires_brainbox(self):
        return True

    @message_handler
    def start_voiceover(self, input: TTSCommand) -> Tuple[BrainBoxService.Command,...]:
        output = []
        for line in input.text:
            inner_task = self.task_factory.create_task(line, input.settings)
            task = BrainBox.ExtendedTask(inner_task, postprocessor=TTSPostprocessor(line))
            message = BrainBoxService.Command(task, metadata=dict(source_message_id=input.envelop.id)).as_reply_to(input)
            output.append(message)
        self.queue.start_tracking(output)
        return tuple(output)

    def start_playing(self) -> Tuple[SoundCommand,...]:
        while self.queue.get_processed_head_length() > 0:
            element = self.queue.deque()
            if element.confirmation.result is None:
                continue
            message_id = element.command.metadata['source_message_id']
            output = element.confirmation.result.with_new_envelop().as_reply_to(message_id)
            self.playing = PlayingElement(message_id, output.envelop.id)
            return (output,)
        return ()

    @message_handler
    def brainbox_finished(self, message: BrainBoxService.Confirmation[SoundCommand]) -> Tuple[SoundCommand,...]:
        if not isinstance(message.result, SoundCommand):
            return ()
        self.queue.track(message)
        if self.playing is None:
            return self.start_playing()
        else:
            return ()

    @message_handler
    def play_finished(self, message: SoundConfirmation) -> tuple[SoundCommand|Confirmation,...]:
        if self.playing is None or not message.is_confirmation_of(self.playing.sound_message_id):
            return ()
        is_last = True
        for element in self.queue.queue:
            if element.command.metadata['source_message_id'] == self.playing.source_message_id:
                is_last = False
                break

        result = []
        if is_last:
            result.append(Confirmation().as_confirmation_for(self.playing.source_message_id))

        self.playing = None
        result.extend(self.start_playing())
        return tuple(result)

    class MockTaskFactory(TTSTaskFactory):
        def create_task(self, s: str, settings: TextInfo) -> BrainBox.ITask:
            return BrainBox.Task(decider='Mock', arguments=dict(text=s))

    @staticmethod
    def brain_box_mock(task: BrainBox.ExtendedTask):
        if task.task.decider != 'Mock':
            raise ValueError("Mock task is expected")
        text = task.task.arguments['text']
        return SoundCommand('FILE: '+text, text)






