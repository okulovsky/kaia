from ..core import IAnnouncementFilter, AnnouncementEnvironment
from .confirmation_announcement import ConfirmationAnnouncementSkill
from datetime import timedelta


class ReinitiateAfterSuccess(IAnnouncementFilter):
    def __init__(self, cooldown: timedelta, no_history_filter: IAnnouncementFilter|None = None):
        self.cooldown = cooldown
        self.no_history_filter = no_history_filter

    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        last_was_feedback = False
        has_history = False
        for rec in env.history:
            if rec.announcement_name != env.announcement_name:
                continue
            has_history = True
            if rec.feedback is not None:
                last_was_feedback = True
                continue
            last_was_feedback = False
            if (env.current_time - rec.timestamp) < self.cooldown:
                return False
        if last_was_feedback:
            return False
        if not has_history and self.no_history_filter is not None:
            return self.no_history_filter.should_announce(env)
        return True


class ReinitiateAfterFeedback(IAnnouncementFilter):
    def __init__(self, cooldown: timedelta):
        self.cooldown = cooldown

    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        has_unfinished = False
        for rec in env.history:
            if rec.announcement_name != env.announcement_name:
                continue
            if rec.feedback is None:
                has_unfinished = False
                continue
            has_unfinished = True
            if rec.feedback == ConfirmationAnnouncementSkill.NEXT_DAY:
                if env.current_time.date() == rec.timestamp.date():
                    return False
            if env.current_time - rec.timestamp < self.cooldown:
                return False
        return has_unfinished


class FollowUp(IAnnouncementFilter):
    def __init__(self, announcement_name_to_follow_up: str, cooldown: timedelta):
        self.announcement_name_to_follow_up = announcement_name_to_follow_up
        self.cooldown = cooldown

    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        found_index = None
        for index in range(len(env.history) -1, -1, -1):
            rec = env.history[index]
            if rec.announcement_name == self.announcement_name_to_follow_up and rec.feedback is None:
                found_index = index
                break

        if found_index is None:
            return False

        for rec in env.history[found_index+1:]:
            if rec.announcement_name == env.announcement_name:
                return False

        return env.current_time - env.history[found_index].timestamp >= self.cooldown

    
class OncePerDay(IAnnouncementFilter):
    def __init__(self, once_for_all_users: bool = False):
        self.once_for_all_users = once_for_all_users

    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        for a in env.history:
            if a.announcement_name == env.announcement_name:
                if a.timestamp.date() == env.current_time.date():
                    if self.once_for_all_users:
                        return False
                    if env.username == a.username:
                        return False
        return True






