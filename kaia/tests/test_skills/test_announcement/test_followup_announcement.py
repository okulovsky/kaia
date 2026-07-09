from unittest import TestCase

from avatar.daemon import UserWalkInService
from eaglesong.core import Automaton, Scenario, Return
from kaia.skills.announcement_skill import ConfirmationAnnouncementSkill, ReinitiateAfterFeedback, ReinitiateAfterSuccess, FollowUp, AnnouncementSkill, Announcement
from kaia.skills.announcement_skill.use_cases.confirmation_announcement import AnnouncementConfirmation, AnnouncementReplies
from grammatron import Template, TemplatesCollection
from datetime import timedelta
from avatar.utils import TestTimeFactory


class LaundryTemplates(TemplatesCollection):
    do_laundry = Template("Do your laundry!")
    take_clothes_away = Template("Take clothes away from the clothing machine!")


POSTPONE_COOLDOWN = timedelta(seconds=10)
DONE_COOLDOWN = timedelta(seconds=30)
FOLLOWUP_COOLDOWN = timedelta(seconds=5)


def S(dtf: TestTimeFactory):
    do_laundry = Announcement(
        'do_laundry',
        ReinitiateAfterSuccess(DONE_COOLDOWN) | ReinitiateAfterFeedback(POSTPONE_COOLDOWN),
        ConfirmationAnnouncementSkill(LaundryTemplates.do_laundry),
    )
    take_clothes_away = Announcement(
        'take_clothes_away',
        FollowUp('do_laundry', FOLLOWUP_COOLDOWN) | ReinitiateAfterFeedback(POSTPONE_COOLDOWN),
        ConfirmationAnnouncementSkill(LaundryTemplates.take_clothes_away),
    )
    skill = AnnouncementSkill([do_laundry, take_clothes_away], datetime_factory=dtf, cooldown=timedelta(seconds=0))
    return Scenario(lambda: Automaton(skill.run, None))


class FollowUpAnnouncementTestCase(TestCase):
    def test_reject_then_accept(self):
        dtf = TestTimeFactory()
        (
            S(dtf)
            .send(UserWalkInService.Event('test'))
            .check(LaundryTemplates.do_laundry(), AnnouncementReplies.will_you_do_it())
            .send(AnnouncementConfirmation.no.utter())
            .check(AnnouncementReplies.i_will_remind(), Return)
            .act(lambda: dtf.shift(10))
            .send(UserWalkInService.Event('test'))
            .check(LaundryTemplates.do_laundry(), AnnouncementReplies.will_you_do_it())
            .send(AnnouncementConfirmation.yes.utter())
            .check(AnnouncementReplies.cool(), Return)
            .act(lambda: dtf.shift(5))
            .send(UserWalkInService.Event('test'))
            .check(LaundryTemplates.take_clothes_away(), AnnouncementReplies.will_you_do_it())
            .send(AnnouncementConfirmation.no.utter())
            .check(AnnouncementReplies.i_will_remind(), Return)
            .act(lambda: dtf.shift(10))
            .send(UserWalkInService.Event('test'))
            .check(LaundryTemplates.take_clothes_away(), AnnouncementReplies.will_you_do_it())
            .send(AnnouncementConfirmation.yes.utter())
            .check(AnnouncementReplies.cool(), Return)
            .validate()
        )
