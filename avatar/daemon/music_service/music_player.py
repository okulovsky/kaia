from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class MusicStatus:
    has_music: bool
    playing: bool
    current_track_summary: str|None

class IMusicPlayer(ABC):
    @abstractmethod
    def start(self, music: Any):
        pass

    @abstractmethod
    def status(self) -> MusicStatus:
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def previous(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def resume(self):
        pass