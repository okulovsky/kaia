import json
from unittest import TestCase
from kaia.eaglesong.core import Automaton, Scenario, Image
from kaia.kaia.skills.change_image_skill import ChangeImageIntents, ChangeImageSkill
from kaia.kaia.skills import KaiaTestAssistant
from kaia.avatar.server import AvatarTestApi, SimpleImageService, AvatarSettings
from kaia.brainbox import MediaLibrary
from kaia.infra import Loc
from kaia.avatar.narrator import DummyNarrator

def check_image(tag):
    def _check(arg):
        print(arg)
        if not isinstance(arg, Image):
            raise ValueError("Wrong type")
        d = json.loads(arg.data)
        if d['tag'] != tag:
            raise ValueError("Wrong image tag")
        return True
    return _check


class ChangeImageTestCase(TestCase):
    def test_change_image(self):
        with Loc.create_temp_file('tests/change_image/library', 'zip', True) as media_library:
            tags = {str(i): {'tag': i} for i in range(3)}
            MediaLibrary.generate(media_library, tags)
            with Loc.create_temp_file('tests/change_image/stats','json') as stats_file:
                image_service = SimpleImageService(media_library, stats_file, False)
                with AvatarTestApi(AvatarSettings(), DummyNarrator(''), None, image_service) as api:
                    (
                        Scenario(lambda: Automaton(KaiaTestAssistant([ChangeImageSkill(api)]), None))
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
