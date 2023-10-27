from .settings import BrainBoxSettings
from ..core import BrainBoxService, BrainBoxWebServer, SimplePlanner, BrainBoxWebApi
from ..deciders.tortoise_tts import TortoiseTTS
from ..deciders.automatic1111 import Automatic1111
from ..deciders.oobabooga import Oobabooga
from ..deciders.tortoise_tts.dub_collector import DubCollector
from ...infra.comm import Sql

class BrainBox:
    def __init__(self):
        self.settings = BrainBoxSettings()

    def create_deciders_dict(self):
        deciders = dict()
        deciders['TortoiseTTS'] = TortoiseTTS(
            self.settings.tortoise_tts.python_path,
            self.settings.tortoise_tts.tortoise_tts_path,
            port = self.settings.tortoise_tts.port
        )
        deciders['Automatic1111'] = Automatic1111(
            self.settings.automatic1111.automatic1111_path,
            self.settings.automatic1111.environment,
            self.settings.automatic1111.port,
        )
        deciders['Oobabooga'] = Oobabooga(
            self.settings.oobabooga.oobabooga_path,
            self.settings.oobabooga.exec_path,
            self.settings.oobabooga.port,
            self.settings.oobabooga.api_port,
            self.settings.oobabooga.model_name
        )

        deciders['DubCollector'] = DubCollector()
        return deciders

    def create_service(self):
        return BrainBoxService(
            self.create_deciders_dict(),
            SimplePlanner(),
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





