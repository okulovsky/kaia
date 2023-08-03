from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_10_recorder import bot as bot_recorder
from demos.eaglesong.example_11_telegram_native import bot as bot_telegram
from kaia.eaglesong.drivers.telegram import TgContext, TgCommand, TgUpdatePackage, TelegramScenario as S
from yo_fluq_ds import Obj

def context_factory():
    return TgContext(None, 123)

def feedback_input_factory(feedback):
    return TgUpdatePackage(TgUpdatePackage.Type.Feedback, feedback, None)

class FiltersTestCase(TestCase):
    def test_filters_bots(self):
        for bot in [bot_telegram, bot_recorder]:
            with self.subTest(bot.name):
                scenario = S(bot.create_telegram_routine(123))
                (
                    scenario
                    .send(S.upd(message___chat___username='text', message___text='/start'))
                    .check(lambda z: isinstance(z, TgCommand) and z.kwargs['text'].startswith('Hello'))
                    .send(S.upd(message___text='test'))
                    .check(lambda z: isinstance(z, TgCommand) and z.kwargs['text']=='test')
                    .validate()
                )