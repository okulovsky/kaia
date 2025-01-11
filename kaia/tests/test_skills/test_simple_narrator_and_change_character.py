import json

from kaia.avatar import AvatarApi, AvatarSettings, NewContentStrategy, TestTaskGenerator, MediaLibraryManager
from unittest import TestCase
from brainbox import MediaLibrary, BrainBoxApi
from brainbox.deciders import FakeFile
from kaia.common import Loc
from kaia.kaia import KaiaAssistant, KaiaContext
from kaia.skills.character_skill import ChangeCharacterIntents, ChangeCharacterSkill
from kaia.skills.change_image_skill import ChangeImageSkill, ChangeImageIntents
from kaia.skills.time import TimeSkill, TimeIntents
from kaia.kaia.translators import VoiceoverTranslator
from eaglesong.core import Automaton, Scenario
from pprint import pprint

def state_to_voice(state):
    return state['character']

def state_to_tags(state):
    return state

class SimpleNarratorCharacterTestCase(TestCase):
    def test_all(self):
        with BrainBoxApi.Test([FakeFile()]) as bb_api:
            with Loc.create_test_file() as media_library:
                tags = {
                    f'{character}_{i}': dict(character=character, image=i)
                    for character in ['character_0','character_1', 'character_2']
                    for i in range(3)
                }
                MediaLibrary.generate(media_library, tags)
                with Loc.create_test_file() as stats_file:
                    settings = AvatarSettings(
                        brain_box_api=bb_api,
                        dubbing_task_generator=TestTaskGenerator(),
                        image_media_library_manager=MediaLibraryManager(NewContentStrategy(), media_library, stats_file)
                    )
                    with AvatarApi.Test(settings) as avatar_api:
                        char_skill = ChangeCharacterSkill(['character_0','character_1','character_2'])
                        assistant = KaiaAssistant([
                            TimeSkill(),
                            ChangeImageSkill(),
                            char_skill
                            ])
                        aut = VoiceoverTranslator(assistant, avatar_api)
                        log = (
                            Scenario(lambda: Automaton(aut, KaiaContext(avatar_api=avatar_api)))
                            .send(TimeIntents.question.utter())
                            .send(ChangeImageIntents.change_image.utter())
                            .send(char_skill.intents.change_character.utter(character='character_1'))
                            .send(TimeIntents.question.utter())
                            .send(ChangeImageIntents.change_image.utter())
                            .send(ChangeCharacterIntents.change_character.utter())
                            .validate()
                            .log
                        )
                        pprint(log)

                        #time
                        self.assertEqual('voice_0', json.loads(log[0].response[1].content)['voice'])

                        #change image
                        self.assertEqual('character_0', json.loads(log[1].response[0].content)['character'])

                        #change character to bob
                        self.assertEqual('character_1', json.loads(log[2].response[0].content)['character'])
                        self.assertEqual('voice_1', json.loads(log[2].response[2].content)['voice'])

                        #time
                        self.assertEqual('voice_1', json.loads(log[3].response[1].content)['voice'])

                        #change image
                        self.assertEqual('character_1', json.loads(log[4].response[0].content)['character'])

                        #change character to random
                        self.assertNotEqual('character_1', json.loads(log[5].response[0].content)['character'])
                        self.assertNotEqual('voice_1', json.loads(log[5].response[2].content)['voice'])





