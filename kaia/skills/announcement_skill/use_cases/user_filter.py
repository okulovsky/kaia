from .. import AnnouncementEnvironment
from ..core import IAnnouncementFilter

class Username(IAnnouncementFilter):
    def __init__(self, *users):
        self.users = users

    def should_announce(self, env: AnnouncementEnvironment) -> bool:
        return env.username in self.users
