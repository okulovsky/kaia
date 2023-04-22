from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_13_timer_2 import bot

class DispatcherTestCase(TestCase):
    def test_dispatcher(self):
        (
            S(bot)
            .send('/start')
            .check(lambda z: z.startswith('This bot will send you an integer every second'))
            .send(TimerTick())
            .check()
            .send('/toggle')
            .check('Timer set to True')
            .send(TimerTick())
            .check(0)
            .send(TimerTick())
            .check(1)
            .send('/toggle')
            .send(TimerTick())
            .check()
            .send('/toggle')
            .send(TimerTick())
            .check(2)
            .validate()
        )


