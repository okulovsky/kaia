import json

from kaia.avatar.server import AvatarTestApi, BrainBoxDubbingService, SimpleImageService, AvatarSettings
from kaia.avatar.narrator import SimpleNarrator
from unittest import TestCase
from kaia.brainbox import BrainBoxTask, BrainBoxTaskPack, MediaLibrary, BrainBoxTestApi, DownloadingPostprocessor
from kaia.brainbox.deciders.fake_dub_decider import FakeDubDecider
from uuid import uuid4
from kaia.infra import Loc, FileIO
from kaia.kaia.skills import KaiaTestAssistant
from kaia.kaia.skills.character_skill import ChangeCharacterIntents, ChangeCharacterSkill
from kaia.kaia.skills.change_image_skill import ChangeImageSkill, ChangeImageIntents
from kaia.kaia.skills.time import TimeSkill, TimeIntents
from kaia.kaia.core import UtterancesTranslator
from kaia.avatar.dub.core import RhasspyAPI
from kaia.eaglesong.core import Automaton, Scenario
from pprint import pprint

def state_to_voice(state):
    return state['character']

def state_to_tags(state):
    return state

def task_generator(s, voice):
    task = BrainBoxTask(str(uuid4()), 'fake_tts', dict(text=s, voice=voice))
    return BrainBoxTaskPack(
        task,
        (),
        DownloadingPostprocessor(0, opener=FileIO.read_json)
    )

class SimpleNarratorCharacterTestCase(TestCase):
    def test_all(self):
        narrator = SimpleNarrator('Alice', dict(Alice='Alice', Bob='Bob', Claire='Claire'))
        services = dict(fake_tts=FakeDubDecider())
        with BrainBoxTestApi(services) as bb_api:
            dubbing_service = BrainBoxDubbingService(task_generator, bb_api)
            with Loc.create_temp_file('tests/change_character/library', 'zip', True) as media_library:
                tags = {
                    f'{character}_{i}': dict(character=character, image=i)
                    for character in ['Alice','Bob', 'Claire']
                    for i in range(3)
                }
                MediaLibrary.generate(media_library, tags)
                with Loc.create_temp_file('tests/change_image/stats', 'json') as stats_file:
                    image_service = SimpleImageService(media_library, stats_file, False)
                    with AvatarTestApi(AvatarSettings(), narrator, dubbing_service, image_service) as avatar_api:
                        char_skill = ChangeCharacterSkill(['Alice','Bob','Claire'], avatar_api)
                        assistant = KaiaTestAssistant([
                            TimeSkill(),
                            ChangeImageSkill(avatar_api),
                            char_skill
                            ])
                        aut = UtterancesTranslator(assistant, RhasspyAPI(None, assistant.get_intents()), avatar_api)
                        log = (
                            Scenario(lambda: Automaton(aut, None))
                            .send(TimeIntents.question.utter())
                            .send(ChangeImageIntents.change_image.utter())
                            .send(char_skill.intents.change_character.utter(character='Bob'))
                            .send(TimeIntents.question.utter())
                            .send(ChangeImageIntents.change_image.utter())
                            .send(ChangeCharacterIntents.change_character.utter())
                            .validate()
                            .log
                        )
                        pprint(log)

                        #time
                        self.assertEqual('Alice', log[0].response[0].data['voice'])

                        #change image
                        self.assertEqual('Alice', json.loads(log[1].response[0].data)['character'])

                        #change character to bob
                        self.assertEqual('Bob', json.loads(log[2].response[0].data)['character'])
                        self.assertEqual('Bob', log[2].response[1].data['voice'])

                        #time
                        self.assertEqual('Bob', log[3].response[0].data['voice'])

                        #change image
                        self.assertEqual('Bob', json.loads(log[4].response[0].data)['character'])

                        #change character to random
                        self.assertNotEquals('Bob', json.loads(log[5].response[0].data)['character'])
                        self.assertNotEquals('Bob', log[5].response[1].data['voice'])





