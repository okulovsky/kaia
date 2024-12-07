from typing import Optional
from ..core import BrainBoxService, BrainBoxWebServer, BrainBoxTestApi, BrainBoxApi, BrainBoxTask
from ...infra.comm import Sql
from ...infra import Loc
from ..core.planers import SimplePlanner


class BrainBoxSettings:
    def __init__(self):
        self.file_cache_path = Loc.temp_folder / 'brainbox_cache'
        self.brainbox_database = Loc.temp_folder / 'queue'
        self.brain_box_web_port = 8090
        self.planner_factory = SimplePlanner
        self.main_iteration_sleep: float = 0.01
        self.raise_exceptions_in_main_cycle: bool = True


class BrainBox:
    Task = BrainBoxTask

    def __init__(self, settings: Optional[BrainBoxSettings] = None):
        self.settings = BrainBoxSettings() if settings is None else settings

    def create_deciders_dict(self):

        from .. import deciders
        deciders_dict = {}
        deciders_dict['TortoiseTTS'] = deciders.TortoiseTTSInstaller(deciders.TortoiseTTSSettings())
        deciders_dict['OpenTTS'] = deciders.OpenTTSInstaller(deciders.OpenTTSSettings())

        comfy_installer = deciders.ComfyUIInstaller(deciders.ComfyUISettings())
        deciders_dict['ComfyUI'] = comfy_installer
        deciders_dict['ComfyUIUtils'] = deciders.ComfyUIUtils(comfy_installer)
        deciders_dict['CoquiTTS'] = deciders.CoquiTTSInstaller(deciders.CoquiTTSSettings())
        deciders_dict['Whisper'] = deciders.WhisperInstaller(deciders.WhisperSettings())
        deciders_dict['RhasspyKaldi'] = deciders.RhasspyKaldiInstaller(deciders.RhasspyKaldiSettings())

        deciders_dict['Collector'] = deciders.Collector()
        deciders_dict['OutputTranslator'] = deciders.OutputTranslator()

        return deciders_dict

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
        return BrainBoxApi(address + f':{self.settings.brain_box_web_port}', self.settings.file_cache_path)


    def create_test_api(self):
        return BrainBoxTestApi(self.create_deciders_dict())


