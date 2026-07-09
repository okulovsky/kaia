from dataclasses import dataclass
from avatar.daemon import UserWalkInService
from .announcement_history import AnnouncementRecord, IAnnouncementHistory, FileAnnouncementHistory
from datetime import datetime, timedelta
from ....assistant import IKaiaSkill, Pushback
from typing import Callable, Iterable
from .proxy_skill import ProxySkill
from .announcement_filter import IAnnouncementFilter, AnnouncementEnvironment



@dataclass
class Announcement:
    name: str
    filter: IAnnouncementFilter
    payload: IKaiaSkill
    priority: int = 0


class AnnouncementSkill(ProxySkill):
    def __init__(self,
                 announcements: list[Announcement],
                 history: IAnnouncementHistory | None = None,
                 datetime_factory: Callable[[], datetime] = datetime.now,
                 cooldown: timedelta = timedelta(seconds=60*5)
                 ):
        self.history = history if history is not None else FileAnnouncementHistory()
        self.announcements = announcements
        self.datetime_factory = datetime_factory
        self.initiated_skill: IKaiaSkill|None = None
        self.initialization_time: datetime = datetime_factory()
        self.cooldown = cooldown


    def get_inner_skills(self) -> Iterable[IKaiaSkill]:
        return (a.payload for a in self.announcements)

    def get_type(self) -> 'IKaiaSkill.Type':
        return IKaiaSkill.Type.MultiLine

    def should_start(self, input) -> bool:
        return isinstance(input, UserWalkInService.Event) and self.initiated_skill is None

    def should_proceed(self, input) -> bool:
        if self.initiated_skill is None:
            return False
        return self.initiated_skill.should_proceed(input)

    def get_runner(self):
        return self.run

    def _find_announcement(self, history, time: datetime, username: str) -> Announcement|None:
        history = self.history.get_records()
        announcements = [
            a for a in self.announcements
            if a.filter.should_announce(AnnouncementEnvironment(a.name, time, history, self.initialization_time, username))
        ]
        announcements = list(sorted(announcements, key=lambda a: a.priority))
        if len(announcements) == 0:
            return None
        return announcements[-1]


    def run(self):
        input: UserWalkInService.Event = yield None
        time = self.datetime_factory()
        history = self.history.get_records()
        if len(history) > 0 and time - history[-1].timestamp < self.cooldown:
            return
        announcement = self._find_announcement(history, time, input.user)
        if announcement is None:
            return
        self.initiated_skill = announcement.payload
        response = yield from self.initiated_skill.get_runner()()
        self.initiated_skill = None
        self.history.add_record(AnnouncementRecord(announcement.name, time, response, input.user))













