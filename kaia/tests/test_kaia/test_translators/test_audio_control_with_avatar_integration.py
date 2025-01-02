from unittest import TestCase
from brainbox import IDecider, BrainBoxApi
from brainbox.deciders import Collector
from kaia.avatar import AvatarApi, AvatarSettings, RecognitionSettings
from kaia.kaia.translators import RecognitionTranslator
from kaia.kaia import AudioCommand
from eaglesong import Scenario, Automaton, Listen


class Whisper(IDecider):
    def transcribe(self, file, model, initial_prompt):
        return f'recognized: {file}'

class Resemblyzer(IDecider):
    def __call__(self, file, model):
        return file[0].upper()


class FakeAudioControl:
    def set_state(self, _):
        pass

class Skill:
    def __init__(self, avatar_api: AvatarApi):
        self.avatar_api = avatar_api

    def __call__(self):
        while True:
            input = yield Listen().store(RecognitionSettings(RecognitionSettings.NLU.Whisper))
            yield dict(input=input, state = self.avatar_api.state_get())

class ACAndAvatarTestCase(TestCase):
    def test_ac_and_avatar_test_integration(self):
        with BrainBoxApi.Test([Whisper(), Resemblyzer(), Collector()]) as bb_api:
            with AvatarApi.Test(AvatarSettings(brain_box_api=bb_api, resemblyzer_model_name='x')) as avatar_api:
                skill = Skill(avatar_api)
                skill = RecognitionTranslator(skill, avatar_api)
                S = Scenario(lambda: Automaton(skill, None))
                (
                    S
                    .send('')
                    .check()
                    .send(AudioCommand('test'))
                    .check(Scenario.stash('response_1'))
                    .send(AudioCommand('atest'))
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









