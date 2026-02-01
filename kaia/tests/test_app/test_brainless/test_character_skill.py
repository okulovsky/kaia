from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.daemon import TextEvent, InitializationEvent, State
from kaia.skills.character_skill import ChangeCharacterIntents
from kaia.tests.helper import Helper



class ActivitySkillTestCase(TestCase):
    def test_activity_skill(self):
        with Loc.create_test_folder() as folder:
            helper = Helper(folder, self, brainless=True)
            with helper.app.get_fork_app(None):
                client = helper.app.create_avatar_client()
                client.initialize()
                client.put(InitializationEvent())
                initial_state = client.query(5).where(lambda z: isinstance(z, State)).first()

                for new_character in helper.settings.avatar_processor.characters:
                    if new_character != initial_state.character:
                        break

                client.put(TextEvent(ChangeCharacterIntents.change_character(new_character)))
                after = client.query(5).where(lambda z: isinstance(z, State)).first()
                self.assertEqual(new_character, after.character)

                client.put(TextEvent(ChangeCharacterIntents.change_character()))
                after = client.query(5).where(lambda z: isinstance(z, State)).first()
                self.assertNotEqual(new_character, after.character)


