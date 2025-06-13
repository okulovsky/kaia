from eaglesong.tests.test_demo.common import *
from eaglesong.demo.example_03_auth_1 import bot as bot_1
from eaglesong.demo.example_04_auth_2 import bot as bot_2
from eaglesong.demo.example_05_auth_3 import bot as bot_3
from eaglesong.demo.example_06_auth_4 import bot as bot_4
import os

class AuthTestCase(TestCase):
    def test_auth_not_ready(self):
        for bot in [bot_1, bot_2, bot_3, bot_4]:
            with self.subTest(bot.name):
                if 'KAIA_TEST_BOT_CHAT_ID' in os.environ:
                    del os.environ['KAIA_TEST_BOT_CHAT_ID']
                (
                    S(bot)
                    .send('/start')
                    .check(lambda z: isinstance(z, Terminate) and z.message.startswith('Please add'))
                    .validate()
                )

    def test_auth_passes(self):
        for bot in [bot_1, bot_2, bot_3, bot_4]:
            with self.subTest(bot.name):
                os.environ['KAIA_TEST_BOT_CHAT_ID'] = '123'
                (
                    S(bot)
                    .send('/start')
                    .check(lambda z: z.startswith('Say anything and I will repeat'))
                    .send('abc')
                    .check('abc')
                    .validate()
                )

    def test_auth_fails(self):
        for bot in [bot_1, bot_2, bot_3, bot_4]:
            with self.subTest(bot.name):
                os.environ['KAIA_TEST_BOT_CHAT_ID'] = '122'
                (
                    S(bot)
                    .send('/start')
                    .check(lambda z: isinstance(z, Terminate) and z.message=='User 123 is not authorized')
                    .validate()
                )