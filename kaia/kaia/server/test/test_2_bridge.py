import requests
from kaia.kaia.audio_control import AudioControlSettings

class AudioCycleToKaiaServerBridge:
    def __init__(self, address, session_id: str):
        self.address = address
        self.session_id = session_id

    def __call__(self, filename):
        address = f'http://{self.address}/command/{self.session_id}/audio_command'
        requests.post(address, json=dict(filename=filename))


class AudioControlBridge:
    def __init__(self, settings: AudioControlSettings):
        self.settings = settings

    def __call__(self):
        cycle = self.settings.create_audio_control()
        cycle.run()
