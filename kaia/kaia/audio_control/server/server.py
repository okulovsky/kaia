from foundation_kaia.marshalling import Server
from .service import AudioControlService

class AudioControlServer(Server):
    def __init__(self, service: AudioControlService, port: int):
        self._audio_service = service
        super().__init__(port, service)
        
    def __call__(self):
        self._audio_service.start()
        super().__call__()
        