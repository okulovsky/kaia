from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_14_task_1 import bot as bot_1
from demos.eaglesong.example_15_task_2 import bot as bot_2
from kaia.infra.tasks import SqlSubprocTaskProcessor, SubprocessConfig
from kaia.eaglesong.amenities.menu import MenuItem
import re

def check_progress_value(s: str, range):
    prefix = 'Progress: '
    ind = s.index(prefix)
    subs = s[ind+len(prefix):ind+len(prefix)+3]
    if not subs in range:
        raise ValueError(f"Subs {subs}, range {range}")
    return True




class DispatcherTestBot(TestCase):
    def setUp(self) -> None:
        self.proc = SqlSubprocTaskProcessor(SubprocessConfig("kaia.infra.tasks:Waiting", [0.1]))
        self.proc.activate()

    def tearDown(self) -> None:
        self.proc.deactivate()

    def test_dispatch(self):
        for bot in [bot_1, bot_2]:
            with self.subTest(bot.name):
                (
                    S(bot, self.proc)
                    .send('/start')
                    .send(6)

                    .send('/status')
                    .check(lambda z: 'Status: received' in z.content)

                    .wait(0.2)
                    .send(SelectedOption(MenuItem.reload_button_text), 'reload#1')
                    .check(Delete, lambda z: 'Status: accepted' in z.content)

                    .wait(0.3)
                    .send(SelectedOption(MenuItem.reload_button_text), 'reload#2')
                    .check(Delete, lambda z: check_progress_value(z.content, ['0.4','0.5','0.6']))

                    .wait(0.5)
                    .send(SelectedOption(MenuItem.reload_button_text), 'reload#3')
                    .check(Delete, lambda z: 'Status: success' in z.content and 'Progress: 1' in z.content)

                    .send(TimerTick())
                    .check(7)

                    .send(SelectedOption(MenuItem.reload_button_text), 'reload#4')
                    .check(Delete, lambda z: 'Status: success' in z.content)

                    .preview()
                )

    def test_dispatch_ticks(self):
        for bot in [bot_1, bot_2]:
            with self.subTest(bot.name):
                (
                    S(bot, self.proc)
                    .send('/start')

                    .send(TimerTick())
                    .check()

                    .send(6)

                    .send(TimerTick())
                    .check(IsThinking)

                    .wait(1)
                    .send(TimerTick())
                    .check(7)

                    .preview()
                )
