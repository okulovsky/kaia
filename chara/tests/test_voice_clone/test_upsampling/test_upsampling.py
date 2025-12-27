from unittest import TestCase
from chara.voice_clone.upsampling import UpsamplingPipeline, StepCache, UpsamplingResult, VerifierResult
from chara.voice_clone.common import VoiceModel, VoiceInference
from pathlib import Path
from foundation_kaia.misc import Loc

from chara.voice_clone.upsampling.upsampling import UpsamplingCache


class MockStep:
    def __init__(self):
        self.buffer = []

    def __call__(self, cache: StepCache, model: VoiceModel, inference: VoiceInference, strs: list[str]):
        self.buffer.append((strs))
        result = []
        for s in strs:
            if s=='1':
                allowed = False
            elif s=='2':
                allowed = len(self.buffer)>1
            else:
                allowed = True
            result.append(UpsamplingResult(
                VerifierResult(
                    0, [], 10, allowed, 0, 0, []
                ),
                s,
                Path(s)
            ))
        cache.write_result(result)

class MockChatterbox:
    def __init__(self):
        super().__init__('Chatterbox')

    def train(self, speaker, sample_file):
        return 'OK'


class UpsamplingPipelineTest(TestCase):
    def test_upsampling(self):
        mock = MockStep()
        pipe = UpsamplingPipeline(Path('test'), None, None, ['1', '2', '3', '4', '5', '6'], mock, 5, 3, 3)
        with Loc.create_test_folder() as folder:
            cache = UpsamplingCache(folder)
            cache.training.write_result([None])
            pipe(cache)

            self.assertEqual(
                [['1', '2', '3'], ['4', '5', '6'], ['1', '2'], ['1']],
                mock.buffer
            )

            result = cache.read_result()
            for i in range(2, 7, 1):
                self.assertIn(str(i), result)
                self.assertEqual(Path(str(i)), result[str(i)])
            self.assertNotIn('1', result)