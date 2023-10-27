from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_09_telegram_native import bot
from kaia.eaglesong.drivers.telegram import TgContext, TgCommand, TgUpdatePackage, TelegramScenario as S
from yo_fluq_ds import Obj

def context_factory():
    return TgContext(None, 123)

def feedback_input_factory(feedback):
    return TgUpdatePackage(TgUpdatePackage.Type.Feedback, feedback)

class FiltersTestCase(TestCase):
    def test_filters_bots(self):
        scenario = S(lambda: bot.create_telegram_automaton(TgContext(None,123)))
        (
            scenario
            .send(S.upd(message___chat___id=123, message___chat___username='user', message___text='/start'))
            .check(
                S.val().send_message(chat_id=123, text='Hello, user. Say anything and I will repeat. Or /start to reset.')
            )
            .send(S.upd(message___text='test'))
            .check(
                S.val().send_message(chat_id=123, text='test')
            )
            .validate()
        )