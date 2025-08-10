from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.daemon import *
from kaia.tests.helper import Helper
from avatar.messaging.amenities import ThreadCollection
from yo_fluq import Query



class FacelessTestCase(TestCase):
    def test_ping(self):
        with Loc.create_test_folder(dont_delete=True) as folder:
            helper = Helper(folder, self)
            with helper.app.get_fork_app(None):
                helper.init()

                for i in range(3):
                    helper.wakeword()
                    c = helper.say('are_you_here')
                    result = helper.parse_reaction(UtteranceSequenceCommand)

                    ThreadCollection.just_print(result)
                    chats = Query.en(result).where(lambda z: isinstance(z, ChatCommand)).to_list()
                    self.assertEqual('Are you here?', chats[0].text)
                    self.assertEqual("Sure, I'm listening.", chats[1].text)

                    sound = Query.en(result).where(lambda z: isinstance(z, SoundCommand)).single()
                    self.assertEqual("Sure, I'm listening.", sound.text)



