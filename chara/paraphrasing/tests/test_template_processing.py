from home.content.characters import *
from chara.paraphrasing import JinjaModel, ParaphraseCase
from unittest import TestCase
from grammatron import *
from avatar.dubbing_service.paraphrase_service import ParaphraseService, ParaphraseServiceSettings
from avatar.media_library_manager import NewContentStrategy, ContentManager, DataClassDataProvider, ExactTagMatcher
from avatar.state import WorldFields, State

INDEX = VariableDub("index", OrdinalDub(10))
DURATION = VariableDub("duration", CardinalDub(100))

class Templates(TemplatesCollection):
    two_varialbes = Template(
        f"The {INDEX} timer is set for {DURATION} minutes"
    )

alice = Character("Alice", Character.Gender.Feminine, "Alice is Alice")
bob = Character("Bob", Character.Gender.Feminine, "Bob is Bob")



class TemplateRestorationTestCase(TestCase):
    def test_template_restoration(self):
        template = Templates.two_varialbes
        infos = JinjaModel.parse_from_template(template)
        self.assertEqual(1, len(infos))
        case = ParaphraseCase(
            infos[0],
            user = alice,
            character = bob,
        )
        s = "Got ya, the {index} timer for {duration} is ticking"
        record = case.create_paraphrase_record(s)
        self.assertEqual(
            'Template: Got ya, the {index} timer for {duration} is ticking',
            str(record.template)
        )

        paraphrase_strategy = NewContentStrategy()

        paraphrase_manager = ContentManager(
            paraphrase_strategy,
            DataClassDataProvider([record]),
            None,
            ExactTagMatcher.SubsetFactory(WorldFields.character, WorldFields.user)
        )

        paraphrase_service = ParaphraseService(ParaphraseServiceSettings(paraphrase_manager))

        ut = template.utter(index=5, duration=20)
        result = paraphrase_service.paraphrase(ut, {WorldFields.character:bob.name, WorldFields.user: alice.name})
        print(result.utterances[0])

