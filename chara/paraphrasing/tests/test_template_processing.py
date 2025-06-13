from home.deployment.kaia.assistant import create_assistant
from home.content.characters import *
from development.paraphrasing.paraphrase_case import ParaphraseInfo, ParaphraseCase
from brainbox import BrainBox
from unittest import TestCase
from eaglesong.templates import *

INDEX = TemplateVariable("index", OrdinalDub(10))
DURATION = TemplateVariable("duration", CardinalDub(100))

class Templates(TemplatesCollection):
    two_varialbes = Template(
        f"The {INDEX} timer is set for {DURATION} minutes"
    )

alice = Character("Alice", Character.Gender.Feminine, "Alice is Alice")
bob = Character("Bob", Character.Gender.Feminine, "Bob is Bob")



class TemplateRestorationTestCase(TestCase):
    def test_template_restoration(self):
        template = Templates.two_varialbes
        infos = ParaphraseInfo.parse_from_template(template)
        self.assertEqual(1, len(infos))
        case = ParaphraseCase(
            infos[0],
            user = alice,
            character = bob,
        )
        s = "Got ya, the {index} timer for {duration} is ticking"
        new_template = case.info.restore_template(s)
        self.assertListEqual([s], new_template.string_templates)
