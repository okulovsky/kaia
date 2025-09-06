import os
import time
from unittest import TestCase
from avatar.messaging import *
from avatar.daemon import SpeakerIdentificationService, BrainBoxService, State, SoundEvent, InitializationEvent
from avatar.server import AvatarApi, AvatarStream, AvatarServerSettings, MessagingComponent
from avatar.server.components import FileCacheComponent
from avatar.daemon.common.vector_identificator import BestOfStrategy, VectorIdentificatorSettings
from yo_fluq import Query
from foundation_kaia.misc import Loc
from pathlib import Path
from yo_fluq import FileIO

def test_sample_to_vector(file: Path|str):
    if isinstance(file, Path):
        file = file.name
    idx = int(file.split('_')[0])
    vector = [0, 0, 0]
    vector[idx] = 1
    return vector


def prepare_folder(folder):
    for idx, i in enumerate(['A', 'B']):
        for j in range(3):
            path = folder / i / f'{idx}_{j}'
            os.makedirs(path.parent, exist_ok=True)
            FileIO.write_bytes(b'', path)


class SpeakerIdentificationTestCase(TestCase):
    def test_speaker_identification(self):
        with AvatarApi.Test() as api:
            with Loc.create_test_folder() as folder:
                prepare_folder(folder)

                state = State()
                service = SpeakerIdentificationService(state, VectorIdentificatorSettings(folder,  BestOfStrategy(4)), api)
                service.vector_identificator.sample_to_vector = test_sample_to_vector
                client = AvatarStream(api).create_client()
                proc = AvatarDaemon(client.clone())
                proc.rules.bind(service)
                proc.debug_and_stop_by_count(1, InitializationEvent())
                self.assertIsNotNone(service.vector_identificator.df)
                df = service.vector_identificator.df.sort_index()
                self.assertEqual(['A','A','A','B','B','B'], list(df.index))
                self.assertEqual([1, 1, 1, 0, 0, 0], list(df[0]))
                self.assertEqual([0, 0, 0, 1, 1, 1], list(df[1]))
                self.assertIsNone(state.user)

                proc.debug_and_stop_by_count(1, SoundEvent('1_10'))
                self.assertEqual('B', state.user)


    def run_identification_retrain(self, target_speaker, speakers: list[str]
                                   ) -> tuple[BrainBoxService.Command, SpeakerIdentificationService.TrainConfirmation]:
        with Loc.create_test_folder() as avatar_cache_folder:
            settings = AvatarServerSettings((
                MessagingComponent(avatar_cache_folder/'db'),
                FileCacheComponent(avatar_cache_folder)
            ))
            with AvatarApi.Test(settings) as api:
                with Loc.create_test_folder() as folder:
                    prepare_folder(folder)

                    state = State()
                    service = SpeakerIdentificationService(state, VectorIdentificatorSettings(folder, BestOfStrategy(4)), api)
                    service.vector_identificator.sample_to_vector = test_sample_to_vector
                    client = AvatarStream(api).create_client()
                    proc = AvatarDaemon(client.clone())
                    proc.rules.bind(service)
                    proc.debug_and_stop_by_count(1, InitializationEvent())

                    for line in speakers:
                        api.file_cache.upload(b'', line)
                        proc.debug_and_stop_by_count(1, SoundEvent(line))

                    result = proc.debug_and_stop_by_all_confirmed(SpeakerIdentificationService.Train(target_speaker))
                    return service.vector_identificator.base, result.messages[-1]


    def test_speaker_identification_retrain(self):
        bs, reply = self.run_identification_retrain('B', ['0_10','1_10','1_11'])
        self.assertEqual(3, len(bs['B']))
        self.assertEqual(3, len(bs['A']))
        self.assertFalse(reply.admit_errors)


    def test_one_retrain(self):
        bs, reply = self.run_identification_retrain('B', ['0_10','0_11','1_10'])
        self.assertTrue(reply.admit_errors)
        self.assertIn('0_11', bs['B'])

    def test_two_retrains(self):
        bs, reply = self.run_identification_retrain('B', ['0_10','0_11','0_12'])
        self.assertTrue(reply.admit_errors)
        self.assertIn('0_11', bs['B'])
        self.assertIn('0_12', bs['B'])

