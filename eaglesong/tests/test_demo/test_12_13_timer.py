from eaglesong.tests.test_demo.common import *
from eaglesong.demo.example_10_timer_1 import bot as bot_1
from eaglesong.demo.example_11_timer_2 import bot as bot_2


class DispatcherTestCase(TestCase):
    def test_timer(self):
        for bot in [bot_1, bot_2]:
            with self.subTest(bot.name):
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

    def test_dispatch(self):
        (
            S(bot_2)
            .send('/start')
            .check(lambda z: z.startswith('This bot will send you an integer every second'))
            .send('/toggle')
            .check('Timer set to True')
            .send(TimerTick())
            .check(0)
            .send('/menu')
            .check(Options)
            .send(SelectedOption('Small talk'))
            .check(Delete, Options)
            .send(TimerTick())
            .check(1)
            .send(SelectedOption('Nice'))
            .check(Delete, "You are handsome!")
            .send('test')
            .check('Unexpected input: test')
            .validate()
        )


