import json

from kaia.avatar import AvatarApi, DubbingService, ImageService, AvatarSettings, NewContentStrategy, TestTaskGenerator, MediaLibraryManager
from unittest import TestCase
from kaia.brainbox import BrainBoxTask, BrainBoxTaskPack, MediaLibrary, BrainBoxTestApi, DownloadingPostprocessor
from kaia.brainbox.deciders.fake_dub_decider import FakeDubDecider
from uuid import uuid4
from kaia.infra import Loc, FileIO
from kaia.kaia.core import KaiaAssistant
from kaia.kaia.skills.character_skill import ChangeCharacterIntents, ChangeCharacterSkill
from kaia.kaia.skills.change_image_skill import ChangeImageSkill, ChangeImageIntents
from kaia.kaia.skills.time import TimeSkill, TimeIntents
from kaia.kaia.translators import VoiceoverTranslator
from kaia.eaglesong.core import Automaton, Scenario
from pprint import pprint

def state_to_voice(state):
    return state['character']

def state_to_tags(state):
    return state

class SimpleNarratorCharacterTestCase(TestCase):
    def test_all(self):
        services = dict(fake_tts=FakeDubDecider())
        with BrainBoxTestApi(services) as bb_api:
            with Loc.create_temp_file('tests/change_character/library', 'zip', True) as media_library:
                tags = {
                    f'{character}_{i}': dict(character=character, image=i)
                    for character in ['character_0','character_1', 'character_2']
                    for i in range(3)
                }
                MediaLibrary.generate(media_library, tags)
                with Loc.create_temp_file('tests/change_image/stats', 'json') as stats_file:
                    settings = AvatarSettings(
                        brain_box_api=bb_api,
                        dubbing_task_generator=TestTaskGenerator(),
                        image_media_library_manager=MediaLibraryManager(NewContentStrategy(), media_library, stats_file)
                    )
                    with AvatarApi.Test(settings) as avatar_api:
                        char_skill = ChangeCharacterSkill(['character_0','character_1','character_2'], avatar_api)
                        assistant = KaiaAssistant([
                            TimeSkill(),
                            ChangeImageSkill(avatar_api),
                            char_skill
                            ])
                        aut = VoiceoverTranslator(assistant, avatar_api)
                        log = (
                            Scenario(lambda: Automaton(aut, None))
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
                        self.assertEqual('voice_0', log[0].response[1].data['voice'])

                        #change image
                        self.assertEqual('character_0', json.loads(log[1].response[0].data)['character'])

                        #change character to bob
                        self.assertEqual('character_1', json.loads(log[2].response[0].data)['character'])
                        self.assertEqual('voice_1', log[2].response[2].data['voice'])

                        #time
                        self.assertEqual('voice_1', log[3].response[1].data['voice'])

                        #change image
                        self.assertEqual('character_1', json.loads(log[4].response[0].data)['character'])

                        #change character to random
                        self.assertNotEqual('character_1', json.loads(log[5].response[0].data)['character'])
                        self.assertNotEqual('voice_1', log[5].response[2].data['voice'])





