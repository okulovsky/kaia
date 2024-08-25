from unittest import TestCase
from kaia.brainbox import IDecider, BrainBoxTestApi
from kaia.brainbox.deciders import Collector
from kaia.avatar import AvatarAPI, AvatarTestApi, AvatarSettings
from kaia.kaia.translators import AudioControlListen, AudioControlHandler, AudioControlCommand
from kaia.eaglesong import Scenario, Automaton


class FakeWhisper(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def transcribe(self, file, initial_prompt):
        return f'recognized: {file}'

class FakeResemblyzer(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, file):
        return file[0].upper()


class FakeAudioControl:
    def set_state(self, _):
        pass

class Skill:
    def __init__(self, avatar_api: AvatarAPI):
        self.avatar_api = avatar_api

    def __call__(self):
        while True:
            input = yield AudioControlListen(True, AudioControlListen.NLU.Whisper, '')
            yield dict(input=input, state = self.avatar_api.state_get())

class ACAndAvatarTestCase(TestCase):
    def test_ac_and_avatar_test_integration(self):
        services = dict(Whisper=FakeWhisper(), Resemblyzer=FakeResemblyzer(), Collector = Collector())
        with BrainBoxTestApi(services) as bb_api:
            with AvatarTestApi(AvatarSettings()) as avatar_api:
                skill = Skill(avatar_api)
                handler = AudioControlHandler(FakeAudioControl(), bb_api, None, lambda:[], 'test', avatar_api)
                skill = handler.create_translator(skill)
                S = Scenario(lambda: Automaton(skill, None))
                (
                    S
                    .send('')
                    .check()
                    .send(AudioControlCommand('test'))
                    .check(Scenario.stash('response_1'))
                    .send(AudioControlCommand('atest'))
                    .check(Scenario.stash('response_2'))
                    .validate()
                )
                self.assertDictEqual(
                    {'input': 'recognized: test', 'state': {'character': 'character_0', 'user': 'T'}},
                    S.stashed_values['response_1']
                )

                self.assertDictEqual(
                    {'input': 'recognized: atest', 'state': {'character': 'character_0', 'user': 'A'}},
                    S.stashed_values['response_2']
                )









