from zoo.group_chatbot.tests.commons import *
from zoo.group_chatbot.skills.admin_reply.admin_reply import AdminReplySkill
from zoo.group_chatbot.skills.admin_reply.banhammer import Banhammer

class BanhammerTestCase(TestCase):
    def get_msg(self):
        return S.upd(
            effective_message___text='A',
            effective_user___id=1,
            effective_message___id=100,
            effective_message___reply_to_message___id = 101,
            effective_message___reply_to_message___from_user___id = 3,
            effective_message___reply_to_message___from_user___name = 'NAME'
        )

    def test_ban(self):
        factory = lambda: datetime(2020,1,1)
        skill = AdminReplySkill(1, 'A', 'X', 'Y', Banhammer(Template('z $user'), 10, factory))
        (
            Test(skill)
            .send(self.get_msg())
            .check(
                S.val().send_message(chat_id=1, text='z NAME', reply_to_message_id=101),
                S.val().restrict_chat_member.kwargs_subset(chat_id=1, user_id=3, until_date=datetime(2020,1,11)),
                Return
            )
            .validate()
        )