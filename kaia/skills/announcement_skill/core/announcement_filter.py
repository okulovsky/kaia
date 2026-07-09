from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
from .announcement_history import AnnouncementRecord

@dataclass
class AnnouncementEnvironment:
    announcement_name: str
    current_time: datetime
    history: list[AnnouncementRecord]
    system_initialization_time: datetime
    username: str


class IAnnouncementFilter(ABC):
    @abstractmethod
    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        pass

    def __or__(self, other):
        return OrAnnouncementFilter(self, other)

    def __and__(self, other):
        return AndAnnouncementFilter(self, other)


class OrAnnouncementFilter(IAnnouncementFilter):
    def __init__(self, first: IAnnouncementFilter, second: IAnnouncementFilter):
        self.first = first
        self.second = second

    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        return self.first.should_announce(env) or self.second.should_announce(env)

class AndAnnouncementFilter(IAnnouncementFilter):
    def __init__(self, first: IAnnouncementFilter, second: IAnnouncementFilter):
        self.first = first
        self.second = second

    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        return self.first.should_announce(env) and self.second.should_announce(env)





