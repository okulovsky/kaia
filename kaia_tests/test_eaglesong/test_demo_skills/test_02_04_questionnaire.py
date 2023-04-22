from kaia_tests.test_eaglesong.test_demo_skills.common import *

from demos.eaglesong.example_02_questionnaire_1 import bot as bot_1
from demos.eaglesong.example_03_questionnaire_2 import bot as bot_2
from demos.eaglesong.example_04_questionnaire_3 import bot as bot_3


class Demo0TestCase(TestCase):
    def test_questionnairs_1(self):
        for bot in [bot_1, bot_2, bot_3]:
            if bot == bot_2:
                by_the_way = [str]
            else:
                by_the_way = []
            with self.subTest(bot.name):
                (
                    S(bot)
                    .send('/start')
                    .check('What is your name?')
                    .send('A')
                    .check('Where are you from, A?')
                    .send('B')
                    .check(* [lambda z: z.startswith('Nice to meet you, A from B!')]+by_the_way+[Return])
                    .validate()
                )







