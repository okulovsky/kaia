from unittest import TestCase
from zoo.group_chatbot.skills.admin_reply.admin_reply import AdminReplySkill
from zoo.group_chatbot.skills.admin_reply.whois import Whois
from kaia.eaglesong.drivers.telegram import TelegramScenario as S
from kaia.eaglesong.core import Return
from string import Template

class WhoisTestCase(TestCase):
    def create_skill(self, whois):
        return AdminReplySkill(1, 'A', 'X', 'Y', whois)


    def test_wrong_message(self):
        whois = self.create_skill(Whois(Template('Z$use_id')))
        (
            S(whois)
            .send(S.upd(effective_message___text='B'))
            .check(Return)
            .validate()
        )

    def test_wrong_customer(self):
        whois = self.create_skill(Whois(Template('Z$use_id')))
        (
            S(whois)
            .send(S.upd(effective_message___text='A', effective_user___id=2, effective_message___id=100))
            .check(
                S.val().send_message(chat_id=1, text='X', reply_to_message_id=100),
                Return
            )
            .validate()
        )

    def test_no_reply_request(self):
        whois = self.create_skill(Whois(Template('Z$use_id')))
        (
            S(whois)
            .send(S.upd(effective_message___text='A', effective_user___id=1, effective_message___id=100, effective_message___reply_to_message = None))
            .check(
                S.val().send_message(chat_id=1, text='Y', reply_to_message_id=100),
                Return
            )
            .validate()
        )

    def get_msg(self):
        return S.upd(
            effective_message___text='A',
            effective_user___id=1,
            effective_message___id=100,
            effective_message___reply_to_message___id = 101,
            effective_message___reply_to_message___from_user___id = 3
        )

    def test_correct_request(self):
        whois = self.create_skill(Whois(Template('Z$user_id')))
        (
            S(whois)
            .send(self.get_msg())
            .check(
                S.val().send_message(chat_id=1, text='Z3', reply_to_message_id=100),
                Return
            )
            .validate()
        )

    def test_correct_request_with_lists(self):
        lists = {
            'K': {"3": "P"},
            "L": {"1": "Q"},
        }
        whois = self.create_skill(Whois(Template('Z$user_id'), Template('U $name V $value'), lists))
        (
            S(whois)
            .send(self.get_msg())
            .check(
                S.val().send_message(chat_id=1, text='Z3\nU K V P', reply_to_message_id=100),
                Return
            )
            .validate()
        )
