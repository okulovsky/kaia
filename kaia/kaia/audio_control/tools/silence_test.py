import sys

from kaia.kaia.audio_control.core import AudioSampleTemplate
from kaia.kaia.audio_control.setup import PorcupinePipeline
from ..setup.settings import AudioControlSettings


class SilenceTest:
    def __init__(self, settings: AudioControlSettings):
        self.settings = settings

    def __call__(self):
        print('Test starts')
        sys.stdout.flush()
        input, output = self.settings.create_input_and_output()
        pipeline = PorcupinePipeline('porcupine', None, None)
        input.start()
        buffer = []
        while True:
            while True:
                data = input.read()
                level = sum(abs(c) for c in data)/len(data)
                buffer.append(level)
                if pipeline.process(data) is not None:
                    break

            for value in buffer[-10:]:
                print(round(value,2), end=' ')
                sys.stdout.flush()

            print("\n\n")



