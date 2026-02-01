import os
import time
from unittest import TestCase
from avatar.messaging import *
from avatar.daemon import SpeakerIdentificationService, BrainBoxService, State, SoundEvent, InitializationEvent
from avatar.server import AvatarApi, AvatarStream, AvatarServerSettings, MessagingComponent
from avatar.server.components import FileCacheComponent
from avatar.daemon.common.vector_identificator import BestOfStrategy
from yo_fluq import Query
from foundation_kaia.misc import Loc
from pathlib import Path
from yo_fluq import FileIO

def make_sample_to_vector(file: Path|str):
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

                service = SpeakerIdentificationService(api, BestOfStrategy(4))
                service.set_resources_folder(folder)
                service.sample_to_vector = make_sample_to_vector
                client = AvatarStream(api).create_client()
                proc = AvatarDaemon(client.clone())
                proc.rules.bind(service)
                proc.debug_and_stop_by_count(1, InitializationEvent())
                self.assertIsNotNone(service.vector_identificator.df)
                df = service.vector_identificator.df.sort_index()
                self.assertEqual(['A','A','A','B','B','B'], list(df.index))
                self.assertEqual([1, 1, 1, 0, 0, 0], list(df[0]))
                self.assertEqual([0, 0, 0, 1, 1, 1], list(df[1]))


                result = proc.debug_and_stop_by_count(1, SpeakerIdentificationService.Command('1_10')).messages
                self.assertEqual('B', result[-1].result)

    def test_train(self):
        with Loc.create_test_folder() as avatar_cache_folder:
            settings = AvatarServerSettings((
                MessagingComponent(avatar_cache_folder/'db'),
                FileCacheComponent(avatar_cache_folder)
            ))
            with AvatarApi.Test(settings) as api:
                with Loc.create_test_folder() as folder:
                    prepare_folder(folder)

                    service = SpeakerIdentificationService(api, BestOfStrategy(4))
                    service.sample_to_vector = make_sample_to_vector
                    service.set_resources_folder(folder)
                    client = AvatarStream(api).create_client()
                    proc = AvatarDaemon(client.clone())
                    proc.rules.bind(service)
                    proc.debug_and_stop_by_count(1, InitializationEvent())

                    file_id = api.file_cache.upload(b'','0_4')
                    proc.debug_and_stop_by_count(1, SpeakerIdentificationService.Train(file_id, 'A'))

                    self.assertIn('0_4', service.vector_identificator.base['A'])

                    proc.debug_and_stop_by_count(1, SpeakerIdentificationService.Train(file_id, 'B'))
                    self.assertIn('0_4', service.vector_identificator.base['B'])
