import json
from unittest import TestCase
from eaglesong.core import Automaton, Scenario
from brainbox import File, MediaLibrary
from kaia.skills.change_image_skill import ChangeImageIntents, ChangeImageSkill
from kaia.kaia import KaiaAssistant, KaiaContext
from avatar import AvatarApi, AvatarSettings, NewContentStrategy, MediaLibraryManager, ImageServiceSettings
from kaia.common import Loc

def check_image(tag):
    def _check(arg, tc: TestCase):
        tc.assertIsInstance(arg, File)
        d = json.loads(arg.content)
        tc.assertEqual(tag, d['tag'])
    return _check


class ChangeImageTestCase(TestCase):
    def test_change_image(self):
        with Loc.create_test_file() as media_library:
            tags = {str(i): {'character': 'character_0', 'tag': i} for i in range(3)}
            MediaLibrary.generate(media_library, tags)
            with Loc.create_test_file() as stats_file:
                manager = MediaLibraryManager(NewContentStrategy(False), media_library, stats_file)
                with AvatarApi.Test(AvatarSettings(image_settings=ImageServiceSettings(manager))) as api:
                    (
                        Scenario(lambda: Automaton(KaiaAssistant([ChangeImageSkill()], raise_exception=False), KaiaContext(avatar_api=api)))
                        .send(ChangeImageIntents.change_image.utter())
                        .check(check_image(0))
                        .send(ChangeImageIntents.change_image.utter())
                        .check(check_image(1))
                        .send(ChangeImageIntents.bad_image.utter())
                        .check(check_image(2))
                        .send(ChangeImageIntents.change_image.utter())
                        .check(check_image(0))
                        .send(ChangeImageIntents.change_image.utter())
                        .check(check_image(2))
                        .validate()
                    )
