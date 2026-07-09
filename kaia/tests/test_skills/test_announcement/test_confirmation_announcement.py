from unittest import TestCase

from avatar.daemon import UserWalkInService
from eaglesong.core import Automaton, Scenario, Return
from kaia.skills.announcement_skill import ConfirmationAnnouncementSkill, ReinitiateAfterFeedback, ReinitiateAfterSuccess, AnnouncementSkill, Announcement
from kaia.skills.announcement_skill.use_cases.confirmation_announcement import AnnouncementConfirmation, AnnouncementReplies
from grammatron import Template, TemplatesCollection
from datetime import timedelta
from avatar.utils import TestTimeFactory


class TestCollection(TemplatesCollection):
    my = Template("Do your exercise!")


DONE_COOLDOWN = timedelta(seconds=30)
POSTPONE_COOLDOWN = timedelta(seconds=10)


def S(dtf: TestTimeFactory):
    announcement = Announcement(
        'exercise',
        ReinitiateAfterSuccess(DONE_COOLDOWN) | ReinitiateAfterFeedback(POSTPONE_COOLDOWN),
        ConfirmationAnnouncementSkill(TestCollection.my),
    )
    skill = AnnouncementSkill([announcement], datetime_factory=dtf, cooldown=timedelta(seconds=0))
    return Scenario(lambda: Automaton(skill.run, None))


class ConfirmationAnnouncementTestCase(TestCase):
    def test_yes(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(UserWalkInService.Event('test'))
            .check(TestCollection.my(), AnnouncementReplies.will_you_do_it())
            .send(AnnouncementConfirmation.yes.utter())
            .check(AnnouncementReplies.cool(), Return)
            .act(lambda: dtf.shift(29))
            .send(UserWalkInService.Event('test'))
            .check(Return)
            .act(lambda: dtf.shift(1))
            .send(UserWalkInService.Event('test'))
            .check(TestCollection.my(), AnnouncementReplies.will_you_do_it())
            .send(AnnouncementConfirmation.yes.utter())
            .check(AnnouncementReplies.cool(), Return)
            .validate()
        )

    def test_no(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(UserWalkInService.Event('test'))
            .check(TestCollection.my(), AnnouncementReplies.will_you_do_it())
            .send(AnnouncementConfirmation.no.utter())
            .check(AnnouncementReplies.i_will_remind(), Return)
            .act(lambda: dtf.shift(9))
            .send(UserWalkInService.Event('test'))
            .check(Return)
            .act(lambda: dtf.shift(1))
            .send(UserWalkInService.Event('test'))
            .check(TestCollection.my(), AnnouncementReplies.will_you_do_it())
            .send(AnnouncementConfirmation.no.utter())
            .check(AnnouncementReplies.i_will_remind(), Return)
            .validate()
        )
