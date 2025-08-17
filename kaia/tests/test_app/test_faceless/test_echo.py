from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.daemon import *
from kaia.tests.helper import Helper
from avatar.messaging.amenities import ThreadCollection
from phonix.daemon import MicStateChangeReport, MicState
from yo_fluq import Query



class FacelessTestCase(TestCase):
    def test_echo(self):
        with Loc.create_test_folder(dont_delete=True) as folder:
            helper = Helper(folder, self)
            with helper.app.get_fork_app(None):

                helper.init()

                helper.wakeword()

                c= helper.say('repeat_after_me')
                result = helper.parse_reaction(UtteranceSequenceCommand)
                ThreadCollection.just_print(result)

                sound = Query.en(result).where(lambda z: isinstance(z, SoundCommand)).single()
                self.assertEqual('Say anything and I will repeat.', sound.text)

                addition = c.query(3).take(2).to_list()
                self.assertEqual(2, len(addition))
                self.assertIsInstance(addition[0], WhisperRecognitionSetup)
                self.assertIsInstance(addition[1], OpenMicCommand)
                c.query(3).take_while(lambda z: not isinstance(z, MicStateChangeReport) or z.state!=MicState.Open).to_list()

                c = helper.say('make_me_a_sandwich')
                result = helper.parse_reaction(UtteranceSequenceCommand)

                sandwich = 'Make me a sandwich.'
                chats = Query.en(result).where(lambda z: isinstance(z, ChatCommand)).to_list()
                for c in chats:
                    self.assertEqual(sandwich, c.text)
                sound = Query.en(result).where(lambda z: isinstance(z, SoundCommand)).single()
                self.assertEqual(sandwich, sound.text)
