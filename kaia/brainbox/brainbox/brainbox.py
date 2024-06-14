from typing import Optional
from ..core import BrainBoxService, BrainBoxWebServer, BrainBoxTestApi, BrainBoxWebApi
from ...infra.comm import Sql
from ...infra import Loc
from ..core.planers import SimplePlanner


class BrainBoxSettings:
    def __init__(self):
        from ..deciders.legacy.automatic1111 import Automatic1111Settings
        from ..deciders.legacy.oobabooga import OobaboogaSettings

        from ..deciders.docker_based import OpenTTSSettings, CoquiTTSSettings, WhisperSettings, TortoiseTTSSettings

        self.automatic1111 = Automatic1111Settings()
        self.oobabooga = OobaboogaSettings()
        self.tortoise_tts = TortoiseTTSSettings()
        self.open_tts = OpenTTSSettings()
        self.coqui_tts = CoquiTTSSettings()
        self.whisper = WhisperSettings()

        self.file_cache_path = Loc.temp_folder / 'brainbox_cache'
        self.brainbox_database = Loc.temp_folder / 'queue'
        self.brain_box_web_port = 8090
        self.planner_factory = SimplePlanner
        self.main_iteration_sleep: float = 0.01
        self.raise_exceptions_in_main_cycle: bool = True


class BrainBox:
    def __init__(self, settings: Optional[BrainBoxSettings] = None):
        self.settings = BrainBoxSettings() if settings is None else settings

    def create_deciders_dict(self):
        from ..deciders.legacy.automatic1111 import Automatic1111
        from ..deciders.legacy.oobabooga import Oobabooga
        from ..deciders.docker_based import OpenTTS, CoquiTTS, Whisper, TortoiseTTS
        from ..deciders.utils.collector import Collector
        from ..deciders.utils.output_translator import OutputTranslator
#
        deciders = dict()
        deciders['Automatic1111'] = Automatic1111(self.settings.automatic1111)
        deciders['Oobabooga'] = Oobabooga(self.settings.oobabooga)

        deciders['TortoiseTTS'] = TortoiseTTS(self.settings.tortoise_tts)
        deciders['OpenTTS'] = OpenTTS(self.settings.open_tts)
        deciders['CoquiTTS'] = CoquiTTS(self.settings.coqui_tts)
        deciders['Whisper'] = Whisper(self.settings.whisper)

        deciders['Collector'] = Collector()
        deciders['OutputTranslator'] = OutputTranslator()

        return deciders

    def create_service(self):
        return BrainBoxService(
            self.create_deciders_dict(),
            self.settings.planner_factory(),
            self.settings.file_cache_path,
            main_iteration_sleep = self.settings.main_iteration_sleep,
            raise_exceptions_in_main_cycle=self.settings.raise_exceptions_in_main_cycle
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


