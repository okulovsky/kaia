import sys
from typing import *
from collections import deque
from abc import ABC, abstractmethod
from dataclasses import dataclass

class IBuffer(ABC):
    @abstractmethod
    def start(self, starting_buffer: Iterable[List[int]]):
        pass

    @abstractmethod
    def add(self, value: List[int]):
        pass

    @abstractmethod
    def collect(self):
        pass



class SimpleBuffer(IBuffer):
    def __init__(self):
        self.buffer: None | list[list[int]] = None

    def start(self, starting_buffer: Iterable[List[int]]):
        self.buffer = list(starting_buffer)

    def add(self, value: List[int]):
        self.buffer.append(value)

    def collect(self):
        return self.buffer



class Bufferer:
    def __init__(self,
                 name: str,
                 buffer: IBuffer,
                 silence_level: float,
                 frames_margin: int,
                 max_queue_length: int,
                 max_leading_silence_length: Optional[int]
                 ):
        self.name = name
        #print(f'creating bufferer {self.name}'); sys.stdout.flush()

        self.buffer = buffer
        self.silence_level = silence_level
        self.frames_margin = frames_margin
        self.max_queue_length = max_queue_length
        self.max_leading_silence_length = max_leading_silence_length

        self.had_voice = False
        self.silence_after_voice: int = 0
        self.leading_silence: int = 0
        self.was_silence = True
        self.queue = deque()
        self.current_silence = True

    def get_state(self):
        return (
            self.name+'  '+
            ('+' if self.had_voice else '-') +
            ('-' if not self.current_silence else '+') +
            str(self.silence_after_voice)+'/'+str(self.frames_margin)
        )

    @dataclass
    class Reply:
        wait: bool
        error: bool
        result: Any


    def observe(self, data) -> Reply:
        level = sum(abs(s) for s in data)/len(data)
        self.current_silence = level <= self.silence_level

        self.queue.append(data)
        while len(self.queue) > self.frames_margin:
            self.queue.popleft()

        if self.had_voice:
            self.buffer.add(data)
            if self.current_silence:
                self.silence_after_voice += 1
                if self.silence_after_voice > self.frames_margin:
                    self.had_voice = False
                    self.silence_after_voice = 0
                    result = self.buffer.collect()
                    #print('RETURNING RESULT'); sys.stdout.flush()
                    return Bufferer.Reply(False, False, result)
            else:
                self.silence_after_voice = 0
        else:
            if not self.current_silence:
                self.had_voice = True
                self.silence_after_voice = 0
                self.buffer.start(self.queue)
            else:
                self.leading_silence+=1
                if self.max_leading_silence_length is not None and self.leading_silence > self.max_leading_silence_length:
                    return Bufferer.Reply(False, True, None)

        #print(self.get_state()); sys.stdout.flush()
        return Bufferer.Reply(True, False, None)

