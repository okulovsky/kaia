from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_16_narrator_1 import bot, main
from kaia.narrator import NarrationContext, NarrationCommand

class Narrator1TestCase(TestCase):
    def test_with_narration_layer(self):
        (
            S(bot, 'fake_proc')
            .send('/start')
            .check('[Improvise] Say something and I will support the conversation!')
            .send('How is your day?')
            .check('[Answer] How is your day?')
            .send('Mine too')
            .check('[Answer] Mine too')
            .validate()
        )

    def test_main_level(self):
        (
            Scenario(lambda: NarrationContext(123), main, printing=Scenario.default_printing)
            .send('/start')
            .check(NarrationCommand.improvise('Say something and I will support the conversation!'))
            .send('How is your day?')
            .check(NarrationCommand.answer('How is your day?'))
            .preview()
        )