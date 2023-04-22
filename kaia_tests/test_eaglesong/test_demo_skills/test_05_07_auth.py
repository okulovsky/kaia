from kaia_tests.test_eaglesong.test_demo_skills.common import *
from demos.eaglesong.example_05_auth_1 import bot as bot_1
from demos.eaglesong.example_06_auth_2 import bot as bot_2
from demos.eaglesong.example_07_auth_3 import bot as bot_3
import os

class AuthTestCase(TestCase):
    def test_auth_not_ready(self):
        for bot in [bot_1, bot_2, bot_3]:
            with self.subTest(bot.name):
                if 'CHAT_ID' in os.environ:
                    del os.environ['CHAT_ID']
                (
                    S(bot)
                    .send('/start')
                    .check(lambda z: isinstance(z, Terminate) and z.message.startswith('Please add'))
                    .validate()
                )

    def test_auth_passes(self):
        for bot in [bot_1, bot_2, bot_3]:
            with self.subTest(bot.name):
                os.environ['CHAT_ID'] = '123'
                (
                    S(bot)
                    .send('/start')
                    .check(lambda z: z.startswith('Hello. Your user_id is 123.'))
                    .send('abc')
                    .check('abc')
                    .validate()
                )

    def test_auth_fails(self):
        for bot in [bot_1, bot_2, bot_3]:
            with self.subTest(bot.name):
                os.environ['CHAT_ID'] = '122'
                (
                    S(bot)
                    .send('/start')
                    .check(lambda z: isinstance(z, Terminate) and z.message=='User 123 is not authorized')
                    .validate()
                )