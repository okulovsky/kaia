from avatar.messaging import *
from avatar.daemon import ParaphraseService, ParaphraseRecord, State, StateToUtterancesApplicationService, \
    InternalTextCommand
from unittest import TestCase
from grammatron import Template, Utterance
from avatar.daemon.common.content_manager import NewContentStrategy
from avatar.daemon.common import TextCommand, InitializationEvent
from foundation_kaia.misc import Loc
from yo_fluq import FileIO

def make(proc: AvatarDaemon, utterance: Utterance) -> str:
    proc.client.put(TextCommand(utterance))
    messages = proc.debug_and_stop_by_empty_queue().messages
    print(messages)
    m = messages[-1]
    if not isinstance(m, InternalTextCommand):
        raise ValueError("Wrong type, expected TextCommand")
    return m.get_text(True)


class ParaphraseTestCase(TestCase):
    def test_paraphrases(self):
        with Loc.create_test_folder() as folder:
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
            FileIO.write_pickle(records, folder/'paraphrases.pkl')

            state = State(character='character_0', language='en')
            proc = AvatarDaemon(TestStream().create_client())
            proc.rules.bind(
                StateToUtterancesApplicationService(state),
            )
            service = ParaphraseService(state, NewContentStrategy(False))
            service.set_resources_folder(folder)
            proc.rules.bind(service, BindingSettings().bind_type(InternalTextCommand).to(StateToUtterancesApplicationService))
            proc.client.put(InitializationEvent())

            m = make(proc, templates[0].utter())
            self.assertEqual('Test_1/character_0/0.', m)

            m = make(proc, templates[0].utter())
            self.assertEqual('Test_1/character_0/1.', m)

            m = make(proc, templates[1].utter())
            self.assertEqual('Test_2/character_0/0.', m)

            state.character = 'character_1'
            m = make(proc, templates[0].utter())
            self.assertEqual('Test_1/character_1/0.', m)

