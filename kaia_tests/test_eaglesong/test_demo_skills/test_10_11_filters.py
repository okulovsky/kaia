from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_10_recorder import bot as bot_recorder
from demos.eaglesong.example_11_telegram_native import bot as bot_telegram
from kaia.eaglesong.drivers.telegram import TgContext, TgCommand, TgUpdatePackage
from yo_fluq_ds import Obj

def context_factory():
    return TgContext(None, 123)

def feedback_input_factory(feedback):
    return TgUpdatePackage(TgUpdatePackage.Type.Feedback, feedback, None)

class FiltersTestCase(TestCase):
    def test_filters_bots(self):
        for bot in [bot_telegram, bot_recorder]:
            with self.subTest(bot.name):
                scenario = Scenario(
                    context_factory,
                    bot.create_telegram_routine(123),
                    feedback_input_factory= feedback_input_factory,
                    printing=Scenario.default_printing
                )
                (
                    scenario
                    .send(TgUpdatePackage(TgUpdatePackage.Type.Start, Obj(message=Obj(chat=Obj(username="test"), text="/start")), None))
                    .check(lambda z: isinstance(z, TgCommand) and z.kwargs['text'].startswith('Hello'))
                    .send(TgUpdatePackage(TgUpdatePackage.Type.Text, Obj(message=Obj(text='test')), None))
                    .check(lambda z: isinstance(z, TgCommand) and z.kwargs['text']=='test')
                    .validate()
                )