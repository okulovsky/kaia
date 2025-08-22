from unittest import TestCase
from kaia.skills.change_image_skill import ChangeImageSkill, ChangeImageIntents, ChangeImageReplies
from avatar.daemon import ImageService
from eaglesong.core import Automaton, Scenario, Return

def S():
    return Scenario(lambda: Automaton(ChangeImageSkill().run, None))



class ChangeImageSkillTestCase(TestCase):
    def test_change_image(self):
        (
            S()
            .send(ChangeImageIntents.change_image())
            .check(
                ImageService.NewImageCommand(),
                Return
            )
            .validate()
        )

    def test_good_image(self):
        (
            S()
            .send(ChangeImageIntents.good_image())
            .check(
                lambda z: isinstance(z, ImageService.ImageFeedback) and z.feedback=='good',
                ChangeImageReplies.thanks(),
                Return
            )
            .validate()
        )

    def test_bad_image(self):
        (
            S()
            .send(ChangeImageIntents.bad_image())
            .check(
                lambda z: isinstance(z, ImageService.ImageFeedback) and z.feedback=='bad',
                ImageService.NewImageCommand,
                Return
            )
            .validate()
        )

    def test_image_description(self):
        (
            S()
            .send(ChangeImageIntents.describe_image())
            .check(
                ImageService.ImageDescriptionCommand,
                Return
            )
            .validate()
        )


