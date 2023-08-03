from unittest import TestCase
from zoo.group_chatbot.skills.notifier import NotifierSkill
from kaia.eaglesong.drivers.telegram import TelegramScenario as S
from kaia.eaglesong.core import Return
from string import Template

class NotifierTestCase(TestCase):
    def test_wrong_user(self):
        skill = NotifierSkill([1], Template('X $user'))
        (
            S(skill)
            .send(S.upd(effective_user___id = 2))
            .check(Return)
            .validate()
        )

    def test_right_user(self):
        skill = NotifierSkill([1], Template('X $user'))
        (
            S(skill)
            .send(S.upd(effective_user___id = 1, effective_user___name = 'A', effective_message___id = 100))
            .check(
                S.val().send_message(chat_id = 1, text = 'X A', reply_to_message_id=100),
                Return
            )
        )
