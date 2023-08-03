from unittest import TestCase
from zoo.group_chatbot.skills.long_messages_restricter import LongMessagesRestricter
from kaia.eaglesong.drivers.telegram import TelegramScenario as S
from kaia.eaglesong.core import Return

def message_factory(user_to_attempt):
    return ','.join([f'{username}/{attempts}' for username, attempts in user_to_attempt.items()])


class TooLongMessagesTestCase(TestCase):
    def test_wrong_customer(self):
        routine = LongMessagesRestricter([1], 10, message_factory)
        (
            S(routine)
            .send(S.upd(effective_user___id = 2))
            .check(Return)
            .validate()
        )

    def test_short_message(self):
        routine = LongMessagesRestricter([1], 10, message_factory)
        (
            S(routine)
            .send(S.upd(effective_user___id = 1, effective_message___text = 'a'*5))
            .check(Return)
            .validate()
        )

    def test_long_message(self):
        routine = LongMessagesRestricter([1], 10)
        (
            S(routine)
            .send(S.upd(effective_user___id = 1, effective_message___text = 'a'*11, effective_message___message_id=123, effective_user___name='X'))
            .check(
                S.val().delete_message(chat_id=1, message_id=123),
                Return
            )
            .validate()
        )

    def msg(self, message_id, length=11, user_id = 1):
        return S.upd(
            effective_user___id = user_id,
            effective_message___text = 'a'*length,
            effective_message___message_id=message_id,
            effective_user___name=f'X{user_id}'
        )

    def test_too_long_message_template(self):
        routine = LongMessagesRestricter([1], 10, message_factory)
        (
            S(routine)
            .send(self.msg(123))
            .check(
                S.val().delete_message(chat_id=1, message_id=123),
                S.val().send_message(chat_id=1, text='X1/1'),
                Return
            )
            .validate()
        )



    def test_two_long_messages(self):
        routine = LongMessagesRestricter([1], 9, message_factory)
        (
            S(routine)
            .send(self.msg(100))
            .check(
                S.val().delete_message(chat_id=1, message_id=100),
                S.val().send_message(chat_id=1, text='X1/1'),
                Return
            )
            .send(self.msg(101))
            .check(
                S.val().delete_message(chat_id=1, message_id=101),
                S.val().send_message(chat_id=1, text='X1/1'),
                Return
            )
            .send(self.msg(102,1))
            .check(
                Return
            )
            .validate()
        )

    def test_long_messages_delay(self):
        routine = LongMessagesRestricter([1,2], 9, message_factory,3)
        (
            S(routine)
            .send(self.msg(100))
            .check(
                S.val().delete_message(chat_id=1, message_id=100),
                S.val().send_message(chat_id=1, text='X1/1'),
                Return
            )
            .send(self.msg(101))
            .check(
                S.val().delete_message(chat_id=1, message_id=101),
                S.val().edit_message_text(text='X1/2', chat_id=1, message_id=10001),
                Return
            )
            .send(self.msg(102,11,2))
            .check(
                S.val().delete_message(chat_id=1, message_id=102),
                S.val().edit_message_text(text='X1/2,X2/1', chat_id=1, message_id=10001),
                Return
            )
            .send(self.msg(103, 1, 1))
            .check(Return)
            .send(self.msg(104, 1, 2))
            .check(Return)
            .send(self.msg(105, 20, 3))
            .check(Return)
            .send(self.msg(106))
            .check(
                S.val().delete_message(chat_id=1, message_id=106),
                S.val().send_message(chat_id=1, text='X1/1'),
                Return
            )
            .send(self.msg(107))
            .check(
                S.val().delete_message(chat_id=1, message_id=107),
                S.val().edit_message_text(text='X1/2', chat_id=1, message_id=10002),
                Return
            )
            .validate()
        )
