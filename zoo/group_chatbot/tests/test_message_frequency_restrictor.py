from unittest import TestCase
from zoo.group_chatbot.skills.message_frequency_restricter import MessageFrequencyRestricter
from kaia.eaglesong.drivers.telegram import TelegramScenario as S
from kaia.eaglesong.core import Return
from datetime import datetime

class MessageFrequencyRestricterTestCase(TestCase):
    def test_wrong_customer(self):
        restricter = MessageFrequencyRestricter([1], 10)
        (
            S(restricter)
            .send(S.upd(effective_user___id = 3))
            .check(Return)
            .validate()
        )

    def test_good_request(self):
        time_factory = lambda: datetime(2020,1,1)
        restricter = MessageFrequencyRestricter([1], 10, time_factory)
        (
            S(restricter)
            .send(S.upd(effective_user___id = 1))
            .check(
                S.val().restrict_chat_member.kwargs_subset(chat_id=1, user_id=1, until_date=datetime(2020,1,1,0,10)),
                Return
            )
            .preview()
        )
