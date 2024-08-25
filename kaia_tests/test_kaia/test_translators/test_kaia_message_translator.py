import pandas as pd
from kaia.kaia.core import KaiaMessage
from kaia.eaglesong import Listen, Scenario, Automaton, IAsserter
from unittest import TestCase
from kaia.kaia.translators import KaiaMessageTranslator
from kaia.avatar import AvatarTestApi, AvatarSettings
from kaia.narrator import World
from kaia.dub import Template


class FakeGuiApi:
    def __init__(self):
        self.buffer = []

    def add_message(self, item):
        self.buffer.append(item)

def echo():
    while True:
        input = yield
        print(f'>> {input}')
        yield input
        yield Listen()

class Adder(IAsserter):
    def __init__(self, api: FakeGuiApi):
        self.api = api
    def assertion(self, actual, test_case: TestCase):
        test_case.assertIsInstance(actual, KaiaMessage)
        self.api.add_message(actual)

class KaiaMessageTranslatorTestCase(TestCase):
    def test_kaia_message_translator(self):
        with AvatarTestApi(AvatarSettings()) as api:
            fake_kaia_api = FakeGuiApi()
            adder = Adder(fake_kaia_api)
            skill = KaiaMessageTranslator(echo, fake_kaia_api, api, lambda z:z+'.png')
            template = Template("Test template")
            S = Scenario(lambda: Automaton(skill, None))
            (
                S
                .send(template())
                .check(adder)
                .act(lambda: api.state_change({World.character.field_name:'character_1'}))
                .send("Test string")
                .check(adder)
                .act(lambda: api.state_change({World.user.field_name:'user'}))
                .send("Test2")
                .check(adder)
                .validate()
            )
            df = pd.DataFrame([z.__dict__ for z in fake_kaia_api.buffer])
            self.assertListEqual([None, 'character_0', None, 'character_1', 'user', 'character_1'], list(df.speaker))
            self.assertListEqual([None, 'character_0.png', None, 'character_1.png','user.png','character_1.png'], list(df.avatar))


