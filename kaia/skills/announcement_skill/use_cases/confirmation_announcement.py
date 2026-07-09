from typing import Iterable
from avatar.daemon import IntentsPack, RhasspyRecognitionSetup, OpenMicCommand
from eaglesong import Listen
from ....assistant import KaiaSkillBase
from grammatron import Template, TemplatesCollection, Utterance


class AnnouncementConfirmation(TemplatesCollection):
    yes = Template("yes", "sure", "okay", "of course")
    no = Template("no", "later", "remind me later", "not now")
    next_day = Template("not today", "next day", "back off")
    already_done = Template("already done", "done", "won't do", "I've done it already")


class AnnouncementReplies(TemplatesCollection):
    will_you_do_it = Template("Will you do it?")
    i_will_remind = Template("I will remind you about it later")
    cool = Template("Great, you're awesome!")


MODEL = 'ConfirmationAnnouncement'

class ConfirmationAnnouncementSkill(KaiaSkillBase):
    NEXT_TIME = 'next_time'
    NEXT_DAY = 'next_day'

    def __init__(self, announcement: Template):
        replies = KaiaSkillBase.class_to_intent_collection(AnnouncementReplies)+(announcement,)
        super().__init__(None, replies)
        self.announcement = announcement

    def get_extended_intents_packs(self) -> Iterable[IntentsPack]:
        return [IntentsPack(
            MODEL,
            (AnnouncementConfirmation.yes, AnnouncementConfirmation.no),
        )]

    def should_proceed(self, input) -> bool:
        return isinstance(input, Utterance)

    def run(self):
        yield self.announcement()
        yield AnnouncementReplies.will_you_do_it()
        input = yield Listen(RhasspyRecognitionSetup(MODEL), OpenMicCommand())
        if input in AnnouncementConfirmation.yes or input in AnnouncementConfirmation.already_done:
            yield AnnouncementReplies.cool()
            return None
        if input in AnnouncementConfirmation.no:
            yield AnnouncementReplies.i_will_remind()
            return ConfirmationAnnouncementSkill.NEXT_TIME
        if input in AnnouncementConfirmation.next_day:
            yield AnnouncementReplies.i_will_remind()
            return ConfirmationAnnouncementSkill.NEXT_DAY





