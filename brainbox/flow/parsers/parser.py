from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable

T = TypeVar("T")

class IParser(ABC, Generic[T]):
    @abstractmethod
    def __call__(self, text: str) -> T:
        pass

    @staticmethod
    def parse_code_block(text):
        buffer = []
        to_buffer = False
        for line in text.split('\n'):
            if line.strip().startswith('```'):
                to_buffer = not to_buffer
                continue
            if to_buffer:
                buffer.append(line)
        return '\n'.join(buffer)


class FunctionalParser(IParser, Generic[T]):
    def __init__(self, function: Callable[[str], T]):
        self.function = function

    def __call__(self, text: str):
        return self.function(text)