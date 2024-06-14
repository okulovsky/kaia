import time
from kaia.kaia.audio_control.core import AudioSampleTemplate
from kaia.kaia.audio_control.setup import PyAudioInput, WavCollectionBuffer
from ..setup.settings import AudioControlSettings
from datetime import datetime
import sys

class EchoTest:
    def __init__(self, settings: AudioControlSettings):
        self.settings = settings


    def play(self, output, template: AudioSampleTemplate):
        output.start_playing(template.to_sample())
        while output.what_is_playing() is not None:
            time.sleep(0.1)

    def __call__(self):
        if self.settings.environment == AudioControlSettings.Environments.PyAudio:
            PyAudioInput.list_input_devices()

        input, output = self.settings.create_input_and_output()
        print('Intro playing')
        self.play(output, self.settings.awake_template)
        print('Intro played')

        wav = WavCollectionBuffer(input.get_mic_data())
        wav.start([])
        begin = datetime.now()

        print('Recording started')
        input.start()
        while True:
            buffer = input.read()
            level = sum(abs(c) for c in buffer)/len(buffer)
            elapsed = (datetime.now() - begin).total_seconds()
            print(f'\r{level}    {elapsed}              ', end='')
            sys.stdout.flush()
            wav.add(buffer)
            if elapsed > 5:
                break
        input.stop()
        print('Recording exited')

        print('Outro playing')
        self.play(output, self.settings.confirmed_template)
        print('Outro played')

        content = wav.collect()

        print('Sample playing')
        self.play(output, AudioSampleTemplate(content))
        print('Sample played')

        print('Exiting now')


