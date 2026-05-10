from typing import Callable
from unittest import TestCase

from avatar.app import AvatarApi
from avatar.daemon import SpeakerIdentificationService, UserWalkInService
from brainbox import BrainBox, ISelfManagingDecider
from foundation_kaia.misc import Loc

from chara import Chara
from chara.common import Samples
from chara.user_identification import VoiceIdentification, FaceIdentification
from chara.user_identification.helpers import UserSampleCase


class IdentificationMock(ISelfManagingDecider):
    def __init__(self, name: str):
        self._name = name

    def get_name(self):
        return self._name

    def _base_vector(self, file) -> list[float]:
        if '_A_' in str(file):
            return [1.0, 0.0, 0.0]
        return [0.0, 1.0, 0.0]

    def vector(self, file) -> list[float]:
        return self._base_vector(file)

    def analyze(self, image) -> list[dict]:
        return [{'embedding': self._base_vector(image)}]


def _annotate_by_name(case: UserSampleCase) -> str:
    return 'A' if '_A_' in case.file else 'B'


def _annotate_flipped(case: UserSampleCase) -> str:
    return 'B' if '_A_' in case.file else 'A'


class PipelinesTestCase(TestCase):
    def _perform_test(self, identification, mock, sample_bytes: bytes):
        prefix = identification.prefix
        suffix = identification.suffix
        service = identification.service

        with Loc.create_test_folder() as avatar_folder:
            with AvatarApi.test(avatar_folder) as avatar_api:
                Chara.Apis.avatar_api = avatar_api

                for i in range(3):
                    avatar_api.cache.upload(f'{prefix}_A_{i}{suffix}', sample_bytes)
                    avatar_api.cache.upload(f'{prefix}_B_{i}{suffix}', sample_bytes)

                with BrainBox.Api.serverless_test([mock]) as brainbox_api:
                    Chara.Apis.brainbox_api = brainbox_api

                    # --- Phase 1: annotation ---
                    with Loc.create_test_folder() as folder:
                        Chara.start(folder)
                        Chara.call(identification.annotation)(('A', 'B'), mock_annotation=_annotate_by_name)

                    resources = avatar_api.resources(service)
                    files = resources.list('current/', glob=True)
                    a_files = sorted(f for f in files if f.startswith('A/'))
                    b_files = sorted(f for f in files if f.startswith('B/'))

                    self.assertEqual(3, len(a_files), f"A files after annotation: {a_files}")
                    self.assertEqual(3, len(b_files), f"B files after annotation: {b_files}")
                    self.assertTrue(all('_A_' in f for f in a_files))
                    self.assertTrue(all('_B_' in f for f in b_files))

                    # --- Phase 2: refinement with flipped annotation ---
                    with Loc.create_test_folder() as folder2:
                        Chara.start(folder2)
                        Chara.call(identification.refinement)(mock_annotation=_annotate_flipped)

                    files2 = resources.list('current/', glob=True)
                    a_files2 = sorted(f for f in files2 if f.startswith('A/'))
                    b_files2 = sorted(f for f in files2 if f.startswith('B/'))

                    self.assertEqual(3, len(a_files2), f"A files after refinement: {a_files2}")
                    self.assertEqual(3, len(b_files2), f"B files after refinement: {b_files2}")
                    self.assertTrue(all('_B_' in f for f in a_files2), f"A slot should hold B-named files: {a_files2}")
                    self.assertTrue(all('_A_' in f for f in b_files2), f"B slot should hold A-named files: {b_files2}")

    def test_voice_identification(self):
        sample_bytes = (Samples.lina / 'lina1.wav').read_bytes()
        self._perform_test(VoiceIdentification(), IdentificationMock('Resemblyzer'), sample_bytes)

    def test_face_identification(self):
        sample_bytes = b'\xff\xd8\xff\xd9'  # minimal JPEG, content ignored by mock
        self._perform_test(FaceIdentification(), IdentificationMock('InsightFace'), sample_bytes)
