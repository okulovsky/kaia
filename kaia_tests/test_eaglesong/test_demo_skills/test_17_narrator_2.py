from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_17_narrator_2 import bot


class Narrator2TestCase(TestCase):
    def setUp(self) -> None:
        self.proc = SqlSubprocTaskProcessor(SubprocessConfig("kaia.infra.tasks:Waiting", [0.01]))
        self.proc.activate()

    def tearDown(self) -> None:
        self.proc.deactivate()

    def test_happy_path(self):
        (
            S(bot, self.proc)
            .send('/start')
            .check()
            .send(TimerTick())
            .check(IsThinking())
            .wait(0.5)
            .send(TimerTick())
            .check('Say something and I will support the conversation! (Improvise, 3 sec)')
            .send(TimerTick())
            .check()
            .send('Hey')
            .check()
            .send(TimerTick())
            .check(IsThinking())
            .wait(1)
            .send(TimerTick())
            .check('Hey (Answer, 3 sec)')
            .validate()
        )

    def test_fallback(self):
        (
            S(bot, self.proc)
            .send('/start')
            .check()
            .send('Hey')
            .check('Oops')
            .preview()
        )
