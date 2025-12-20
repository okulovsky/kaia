import pickle

from avatar.messaging import *
from avatar.daemon import ParaphraseService, ParaphraseRecord, State, StateToUtterancesApplicationService
from unittest import TestCase
from grammatron import Template, Utterance
from avatar.daemon.common.content_manager import NewContentStrategy
from avatar.daemon.common import UtteranceSequenceCommand, PlayableTextMessage, InitializationEvent
from foundation_kaia.misc import Loc
from avatar.server import AvatarApi, AvatarServerSettings, MessagingComponent, AvatarStream
from avatar.server.components import ResourcesComponent


class ParaphraseTestCase(TestCase):

    def test_paraphrase_integration(self):
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


        with Loc.create_test_folder() as folder:
            settings = AvatarServerSettings((
                MessagingComponent(),
                ResourcesComponent(folder)
            ))
            with AvatarApi.Test(settings) as api:
                api.resources(ParaphraseService).upload(
                    pickle.dumps(records),
                    "paraphrases_000.pkl"
                )

                state = State(character='character_0', language='en')
                stream = AvatarStream(api)
                proc = AvatarDaemon(stream.create_client(), working_folder=folder)
                proc.rules.bind(StateToUtterancesApplicationService(state))
                service = ParaphraseService(state, NewContentStrategy(False))
                proc.rules.bind(service, BindingSettings().bind_type(PlayableTextMessage).to_all_except(ParaphraseService))
                proc.run_in_thread()

                client = stream.create_client().scroll_to_end()
                api.messaging.add('default', InitializationEvent())
                api.messaging.add('default', UtteranceSequenceCommand(templates[0].utter()))
                result = client.query().where(lambda z: isinstance(z, PlayableTextMessage)).take(2).to_list()

                self.assertEqual('Test_1/character_0/0.', result[-1].text.get_text(True, None))

                self.assertTrue(api.resources(ParaphraseService).is_file('paraphrases-feedback.json'))
                self.assertTrue(folder/'ParaphrasesService/paraphrases-feedback.json')






