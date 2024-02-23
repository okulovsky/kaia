from typing import Optional
from ..core import BrainBoxService, BrainBoxWebServer, BrainBoxTestApi, BrainBoxWebApi
from ...infra.comm import Sql
from ...infra import Loc
from ..core.planers import SimplePlanner


class BrainBoxSettings:
    def __init__(self):
        from ..deciders.automatic1111 import Automatic1111Settings
        from ..deciders.oobabooga import OobaboogaSettings
        from ..deciders.open_tts import OpenTTSSettings
        from ..deciders.tortoise_tts import TortoiseTTSSettings
        from ..deciders.open_voice import OpenVoiceSettings

        self.automatic1111 = Automatic1111Settings()
        self.oobabooga = OobaboogaSettings()
        self.tortoise_tts = TortoiseTTSSettings()
        self.open_voice = OpenVoiceSettings()
        self.open_tts = OpenTTSSettings()
        self.file_cache_path = Loc.temp_folder / 'brainbox_cache'
        self.brainbox_database = Loc.temp_folder / 'queue'
        self.brain_box_web_port = 8090
        self.planner_factory = SimplePlanner


class BrainBox:
    def __init__(self, settings: Optional[BrainBoxSettings] = None):
        self.settings = BrainBoxSettings() if settings is None else settings

    def create_deciders_dict(self):
        from ..deciders.tortoise_tts import TortoiseTTS
        from ..deciders.automatic1111 import Automatic1111
        from ..deciders.collector import Collector
        from ..deciders.open_tts import OpenTTS
        from ..deciders.oobabooga import Oobabooga
        from ..deciders.open_voice import OpenVoice



        deciders = dict()
        deciders['TortoiseTTS'] = TortoiseTTS(self.settings.tortoise_tts)
        deciders['Automatic1111'] = Automatic1111(self.settings.automatic1111)
        deciders['Oobabooga'] = Oobabooga(self.settings.oobabooga)
        deciders['OpenTTS'] = OpenTTS(self.settings.open_tts)
        deciders['OpenVoice'] = OpenVoice(self.settings.open_voice)
        deciders['Collector'] = Collector()
        return deciders

    def create_service(self):
        return BrainBoxService(
            self.create_deciders_dict(),
            self.settings.planner_factory(),
            self.settings.file_cache_path
        )

    def create_web_service(self, comm):
        if comm is None:
            comm = Sql.file(self.settings.brainbox_database)

        service = self.create_service()

        return BrainBoxWebServer(
            self.settings.brain_box_web_port,
            comm,
            self.settings.file_cache_path,
            service
        )

    def create_api(self, address):
        return BrainBoxWebApi(address+f':{self.settings.brain_box_web_port}', self.settings.file_cache_path)


    def create_test_api(self):
        return BrainBoxTestApi(self.create_deciders_dict())


