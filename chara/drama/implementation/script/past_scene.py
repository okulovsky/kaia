from typing import *
from ..scene import Message
from .file_manager import FileManager
import json
from dataclasses import dataclass

@dataclass
class PastScene:
    messages: tuple[Message|dict,...]

    def messages_only(self):
        return tuple(m for m in self.messages if isinstance(m, Message))

    def find_tags(self, *tags):
        for message in self.messages:
            if isinstance(message, dict):
                for key, value in message.items():
                    if key in tags:
                        yield value



@dataclass
class PastPlay:
    past_scenes: tuple[PastScene,...]
    unfinished_scene: PastScene
    request: str|None

    @staticmethod
    def from_messages(messages: Iterable[Union[Message,dict]], request: str|None = None):
        scenes = []
        current_messages = []
        for message in messages:
            current_messages.append(message)
            if isinstance(message, dict) and 'finished' in message:
                scenes.append(tuple(current_messages))
                current_messages = []
        scenes = tuple(PastScene(s) for s in scenes)
        return PastPlay(scenes, PastScene(tuple(current_messages)), request)



    @staticmethod
    def parse(manager: FileManager):
        current = manager.sections.get('Play', [])
        current_messages = []
        request = None
        for line in current:
            if line.strip() == '':
                continue
            elif line.startswith('{'):
                fields = json.loads(line)
                current_messages.append(fields)
            elif line.startswith('!'):
                request = line[1:]
            else:
                current_messages.append(Message.parse(line))
        return PastPlay.from_messages(current_messages, request)


