from abc import ABC, abstractmethod
from dataclasses import dataclass
from .dto import AudioSample
from collections import deque
from datetime import datetime

@dataclass
class AudioControlDebugItem:
    audio_playing: None|AudioSample
    mic_working: bool
    data: None|list[int]
    pipeline_name: str
    pipeline_state: str


class IAudioControlDebugConsole(ABC):
    @abstractmethod
    def observe(self, item: AudioControlDebugItem):
        pass


class ConsoleControlDebugConsole(IAudioControlDebugConsole):
    def __init__(self):
        self.counter = 0
        self.queue = deque()

    def observe(self, item: AudioControlDebugItem):
        playing = ''
        if item.audio_playing is not None:
            playing = '🔊'
            if item.audio_playing.template.title is not None:
                playing += item.audio_playing.template.title

        mic_level = '-'*5
        if item.mic_working and item.data is not None:
            value = sum(abs(c) for c in item.data) / len(item.data)
            self.queue.append(value)
            mic_level = str(int(sum(self.queue)/len(self.queue)))
        else:
            self.queue.append(0)
        while len(self.queue)>100:
            self.queue.popleft()

        pipeline = ''
        if item.pipeline_name is not None:
            pipeline = item.pipeline_name

        state = ''
        if item.pipeline_state is not None:
            state = item.pipeline_state

        prefix = str(datetime.now().time())

        print(f'\r{prefix} {playing}\t{mic_level}\t{pipeline}\t{state}                                 ',end='')


