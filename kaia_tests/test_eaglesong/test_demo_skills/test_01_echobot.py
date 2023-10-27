from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_01_echobot import bot

class Demo0TestCase(TestCase):
    def test_echobot(self):
        (
            S(bot)
            .send('/start')
            .check(lambda z: z.startswith('Say anything and I will repeat.'))
            .send('abc')
            .check('abc')
            .validate()
         )

    def test_echobot_fails(self):
        self.assertRaises(ValueError,lambda:
        S(bot)
          .send('/start')
          .check(lambda z: z.startswith('Hey'))
          .validate()
        )

