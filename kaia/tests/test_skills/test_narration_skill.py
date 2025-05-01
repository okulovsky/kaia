from unittest import TestCase
from eaglesong.core import Automaton, Scenario
from brainbox import File, MediaLibrary
from kaia.skills import NarrationSkill, InitializationSkill
from kaia.kaia import KaiaAssistant, KaiaContext, InitializationCommand, TestTimeFactory
from kaia.avatar import (
    AvatarApi, AvatarSettings, NewContentStrategy, MediaLibraryManager, InitialStateFactory, KnownFields,
    NarrationSettings, ImageServiceSettings
)
from kaia.common import Loc

def check_image(name):
    def _check(arg, tc: TestCase):
        tc.assertIsInstance(arg, File)
        tc.assertEqual(name, arg.name)
    return _check

class ChangeImageTestCase(TestCase):
    def run_in_setup(self, action):
        with Loc.create_test_file() as media_library:
            characters = ('A', 'B')
            activities = ('1', '2', '3')
            tags = {
                f'{character}-{activity}': {KnownFields.character: character, KnownFields.activity: activity}
                for character in characters
                for activity in activities
            }
            MediaLibrary.generate(media_library, tags)

            with Loc.create_test_file() as stats_file:
                manager = MediaLibraryManager(NewContentStrategy(False), media_library, stats_file)
                settings = AvatarSettings(
                    initial_state_factory=InitialStateFactory.Simple({KnownFields.character: characters[0]}),
                    image_settings=ImageServiceSettings(manager),
                    narration_settings=NarrationSettings(
                        characters,
                        activities,
                        welcome_utterance='Hello',
                        randomize=False,
                        time_between_images_in_seconds=0
                    )
                )
                with AvatarApi.Test(settings) as api:
                    scenario = Scenario(
                        lambda: Automaton(
                            KaiaAssistant([
                                NarrationSkill(pause_between_checks_in_seconds=10),
                                InitializationSkill(),
                                ],
                                raise_exception=False
                            ),
                            KaiaContext(avatar_api=api)
                        )
                    )

                    action(scenario)

    def action_initialization(self, scenario: Scenario):
        (
            scenario
            .send(InitializationCommand())
            .check(check_image('B-1'), 'Hello')
            .send(InitializationCommand())
            .check(check_image('A-2'), 'Hello')
            .validate()
        )

    def test_initialization(self):
        self.run_in_setup(self.action_initialization)

    def action_tick(self, scenario: Scenario):
        t = TestTimeFactory()
        (
            scenario
            .send(InitializationCommand())
            .check(check_image('B-1'), 'Hello')
            .send(t.delta(0).tick())
            .check()
            .send(t.delta(9).tick())
            .check()
            .send(t.delta(10).tick())
            .check(check_image('B-2'))
            .validate()
        )

    def test_tick(self):
        self.run_in_setup(self.action_tick)


