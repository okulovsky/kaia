from ....assistant import SingleLineKaiaSkill
from grammatron import Template


class SimpleAnnouncementSkill(SingleLineKaiaSkill):
    def __init__(self, announcement: Template, pushback = None):
        super().__init__(None, [announcement], None)
        self.announcement = announcement
        self.pushback = pushback

    def run(self):
        yield self.announcement()
        return self.pushback

