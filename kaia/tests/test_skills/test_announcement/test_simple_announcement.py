from unittest import TestCase

from avatar.daemon import UserWalkInService
from eaglesong.core import Automaton, Scenario, Return
from kaia.skills.announcement_skill import SimpleAnnouncementSkill, Announcement, AnnouncementSkill, ReinitiateAfterSuccess
from grammatron import Template, TemplatesCollection
from datetime import timedelta
from avatar.utils import TestTimeFactory


class TestCollection(TemplatesCollection):
    my = Template("My announcement")


def S(dtf: TestTimeFactory):
    announcement = Announcement(
        'test',
        ReinitiateAfterSuccess(timedelta(seconds=30)),
        SimpleAnnouncementSkill(TestCollection.my),
    )
    skill = AnnouncementSkill([announcement], datetime_factory=dtf, cooldown=timedelta(seconds=0))
    return Scenario(lambda: Automaton(skill.run, None))

class SimpleAnnouncementTestCase(TestCase):
    def test_echo(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(UserWalkInService.Event('test'))
            .check(TestCollection.my(), Return)
            .act(lambda: dtf.shift(29))
            .send(UserWalkInService.Event('test'))
            .check(Return)
            .act(lambda: dtf.shift(1))
            .send(UserWalkInService.Event('test'))
            .check(TestCollection.my(), Return)
            .validate()
        )
