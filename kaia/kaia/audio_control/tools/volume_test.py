import time
from kaia.kaia.audio_control.core import AudioSampleTemplate
from kaia.kaia.audio_control.setup import PyAudioInput, WavCollectionBuffer
from ..setup.settings import AudioControlSettings
from datetime import datetime
import sys

class VolumeTest:
    def __init__(self, settings: AudioControlSettings, volumes: list[float]):
        self.settings = settings
        self.volumes = volumes



    def play(self, output, template: AudioSampleTemplate):
        output.start_playing(template.to_sample())
        while True:
            result = output.what_is_playing()
            if result is None:
                break
            time.sleep(0.1)

    def __call__(self):
        print('Volume test starts')
        _, output = self.settings.create_input_and_output()
        for volume in self.volumes:
            output.set_volume(volume)
            print(f'Volume set to {volume}, sounds starts')
            self.play(output, self.settings.awake_template)
            print('Sounds ended')
            time.sleep(5)

