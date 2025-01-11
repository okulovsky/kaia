import os

from ..wav_streaming import WavStreamingApi, WavStreamingServer, WavServerSettings, WavApiSettings
from ..server import AudioControlApi, MicState, AudioControlServer
from ..audio_control_cycle import AudioControlSettings
from kaia.infra import FileIO, Loc
from kaia.infra.app import KaiaApp
from pathlib import Path

class AudioControlTestTool:
    def __init__(self,
                 wav_streaming_api: WavStreamingApi|None = None,
                 audio_control_api: AudioControlApi|None = None,
                 audio_settings: AudioControlSettings|None = None,
                 run_play_server: bool = False
                 ):
        self.wav_streaming_api = wav_streaming_api
        self.audio_control_api = audio_control_api
        self.audio_settings = audio_settings
        if self.audio_settings is None:
            if wav_streaming_api is None or audio_control_api is None:
                raise ValueError("If one of the api is not set, settings must be present")

    def __call__(self):
        self.create_app().run()

    def create_app(self):
        app = KaiaApp()

        if self.wav_streaming_api is None:
            folder = Loc.temp_folder/'wav_streaming_in_test'
            os.makedirs(folder, exist_ok=True)
            wav_server = WavStreamingServer(WavServerSettings(folder))
            app.add_multiproc_service(wav_server)
            self.wav_streaming_api = WavStreamingApi(WavApiSettings(self.audio_settings.sample_rate, self.audio_settings.frame_length))

        if self.audio_control_api is None:
            audio_server = AudioControlServer(self.audio_settings.create_audio_control, self.audio_settings.port)
            app.add_multiproc_service(audio_server)
            self.audio_control_api = AudioControlApi(f'127.0.0.1:{self.audio_settings.port}')

        app.set_primary_service(self.echo_test)
        return app

    def echo_test(self):
        print('Waiting for audio control awailability... ', end='')
        self.audio_control_api.wait_for_availability()
        print('DONE')
        open = True
        while True:
            print('Waiting for sample... ', end='')
            filename = self.audio_control_api.wait_for_uploaded_filename()
            print('DONE')

            print('Downloading sample... ', end='')
            bts = self.wav_streaming_api.download(filename)
            print('DONE')

            print('Playing sample back... ', end='')
            self.audio_control_api.play_audio(bts)
            print('DONE')

            if open:
                print('Sending OPEN command... ', end='')
                self.audio_control_api.set_state(MicState.Open)
                print('DONE')
            open = not open
