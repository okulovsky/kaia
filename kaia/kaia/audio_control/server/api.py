from .interface import IAudioControlApi
from foundation_kaia.marshalling import Api, bind_to_api, TestApi
from .service import AudioControlService
from .server import AudioControlServer

@bind_to_api(AudioControlService)
class AudioControlApi(Api, IAudioControlApi):
    def __init__(self, address):
        super().__init__(address)

    class Test(TestApi['AudioControlApi']):
        def __init__(self, factory, port):
            server = AudioControlServer(AudioControlService(factory), port)
            super().__init__(AudioControlApi, server)
