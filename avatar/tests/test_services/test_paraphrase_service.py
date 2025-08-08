from avatar.messaging import *
from avatar.services import ParaphraseService, ParaphraseRecord, State, StateToUtterancesApplicationService
from unittest import TestCase
from grammatron import Template, Utterance
from avatar.services.common.content_manager import ContentManager, DataClassDataProvider
from avatar.services.common import UtteranceSequenceCommand, PlayableTextMessage


def test(proc: AvatarProcessor, utterance: Utterance) -> str:
    proc.client.put(UtteranceSequenceCommand(utterance))
    messages = proc.debug_and_stop_by_empty_queue().messages
    m = messages[-1]
    if not isinstance(m, PlayableTextMessage):
        raise ValueError("Wrong type, expected PlayableTextMessage")
    return m.text.get_text(True,'en')


class ParaphraseTestCase(TestCase):
    def test_paraphrases(self):
        templates = [
            Template("Original text 1").with_name('test_1').context(),
            Template("Original text 2").with_name('test_2').context()
        ]
        records = [
            ParaphraseRecord(
                f'{template.get_name()}/{character}/{option}',
                Template(f'{template.get_name()}/{character}/{option}'),
                template.get_name(),
                '',
                'en',
                character,
            )
            for template in templates
            for character in ['character_0', 'character_1']
            for option in range(3)
        ]

        manager = ContentManager(DataClassDataProvider(records))

        state = State(character='character_0', language='en')
        proc = AvatarProcessor(TestStream().create_client())
        proc.rules.bind(StateToUtterancesApplicationService(state))
        proc.rules.add(
            ParaphraseService(state, manager),
            RuleConnector(
                PlayableTextMessage,
                exclude_publisher_prefixes=('ParaphraseService',))
        )

        m = test(proc, templates[0].utter())
        self.assertEqual('Test_1/character_0/0.', m)

        m = test(proc, templates[0].utter())
        self.assertEqual('Test_1/character_0/1.', m)

        m = test(proc, templates[1].utter())
        self.assertEqual('Test_2/character_0/0.', m)

        state.character = 'character_1'
        m = test(proc, templates[0].utter())
        self.assertEqual('Test_1/character_1/0.', m)



    def no_test(self):


        preview = api.dub(templates[0].utter())
        self.assertEqual('Test_1/character_0/0.', preview.full_text)

        preview = api.dub(templates[0]())
        self.assertEqual('Test_1/character_0/1.', preview.full_text)

        preview = api.dub(templates[1].utter())
        self.assertEqual('Test_2/character_0/0.', preview.full_text)

        api.state_change({WorldFields.character: 'character_1'})
        preview = api.dub(templates[0].utter())
        self.assertEqual('Test_1/character_1/0.', preview.full_text)

        api.state_change({'mood': 'sad'})
        preview = api.dub(templates[0].utter())
        self.assertEqual('Test_1/character_1/1.', preview.full_text)

        api.state_change({WorldFields.character:'character_2'})
        preview = api.dub(templates[0].utter())
        self.assertEqual('Original text 1.', preview.full_text)





