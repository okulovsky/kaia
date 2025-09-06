from avatar.daemon import UserWalkInService, ChatCommand
from kaia.assistant import SingleLineKaiaSkill, Feedback
from typing import cast, Iterable, Callable, Optional
from dataclasses import dataclass
from foundation_kaia.misc.scheduled_time import IRepetition
from datetime import time, timedelta, datetime
from grammatron import *
from loguru import logger



@dataclass
class WalkInAnnouncement:
    user: str
    from_time: time
    to_time: time
    repetition: IRepetition
    cooldown: timedelta
    announcement: str|Template|Feedback|Utterance|Iterable[str|Template|Feedback|Utterance]

    def get_announcement(self) -> Iterable[str|Template|Feedback]:
        an = self.announcement
        if isinstance(an, (str, Template, Feedback, Utterance)):
            an = [an]
        else:
            an = list(an)
        for item in an:
            if isinstance(item, Template):
                yield item()
            else:
                yield item


@dataclass
class PastAnnouncement:
    timestamp: datetime
    announcement: WalkInAnnouncement


class WalkInSkill(SingleLineKaiaSkill):
    def __init__(self,
                 announcements: list[WalkInAnnouncement],
                 notify_message: Optional[Callable[[str], ChatCommand]] = None):
        self.announcements = announcements
        self.past_announcements: list[PastAnnouncement] = []
        self.notify_message = notify_message

        super().__init__()

    def should_start(self, input) -> False:
        return isinstance(input, UserWalkInService.Event)

    def get_replies(self) -> Iterable[TemplateBase]:
        return [a.template for _ in self.announcements for a in _.get_announcement() if isinstance(a, Utterance)]

    def _test_announcement(self, user, current_time: datetime, announcement: WalkInAnnouncement) -> str|None:
        if announcement.user != user:
            return f'USER, {announcement.user} != {user}'
        if current_time.time() < announcement.from_time:
            return f'TOO_EARLY, {current_time.time()} < {announcement.from_time}'
        if current_time.time() > announcement.to_time:
            return f'TOO_LATE, {current_time.time()} > {announcement.to_time}'
        if not announcement.repetition.accepts_date(current_time.date()):
            return f"DATE REJECTED {current_time.date()}"

        past_of_this = None
        for p in self.past_announcements:
            if p.announcement is announcement:
                past_of_this = p
        if past_of_this is not None:
            delta = current_time - past_of_this.timestamp
            if delta < announcement.cooldown:
                return f"COOLDOWN {delta} < {announcement.cooldown}"
        return None

    def run(self):
        event = yield None
        event = cast(UserWalkInService.Event, event)
        user = event.user
        logger.info(f"Walk-in skill entered: {user}")

        if self.notify_message is not None:
            yield self.notify_message(user)

        for announcement in self.announcements:
            test_result = self._test_announcement(user, event.envelop.timestamp, announcement)
            if test_result is not None:
                logger.info(f"Announcement {announcement} rejected {test_result}")
            else:
                logger.info(f'Announcement {announcement} accepted')
                self.past_announcements.append(PastAnnouncement(event.envelop.timestamp, announcement))
                yield from announcement.get_announcement()
                break


