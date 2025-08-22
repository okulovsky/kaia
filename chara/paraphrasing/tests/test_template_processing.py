from chara.paraphrasing import JinjaModel, ParaphraseCase
from unittest import TestCase
from grammatron import *
from avatar.daemon import Character, ParaphraseService, State, PlayableTextMessage, TextInfo, UtteranceSequenceCommand
from avatar.daemon.common.content_manager import ContentManager, DataClassDataProvider



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
            language='en'
        )
        s = "Got ya, the {index} timer for {duration} is ticking"
        record = case.create_paraphrase_record(s)
        self.assertEqual(
            'Template: Got ya, the {index} timer for {duration} is ticking',
            str(record.template)
        )

        paraphrase_manager = ContentManager(
            DataClassDataProvider([record]),
        )

        state = State()
        paraphrase_service = ParaphraseService(state, paraphrase_manager)

        ut = template.utter(index=5, duration=20)

        message = PlayableTextMessage(
            UtteranceSequenceCommand(ut),
            TextInfo(
                bob.name,
                'en'
            )
        )
        state.character = bob.name
        state.user = alice.name

        result = paraphrase_service.paraphrase(message)
        self.assertEqual(
            'Got ya, the fifth timer for twenty is ticking.',
            result.text.get_text(True, 'en')
        )


