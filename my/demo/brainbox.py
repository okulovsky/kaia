from kaia.brainbox import (
    BrainBoxWebServer, BrainBoxService, BrainBox
)
from kaia.brainbox.core.planers import AlwaysOnPlanner
from kaia.brainbox.deciders.docker_based.open_tts import OpenTTS, OpenTTSSettings
from kaia.infra import Loc, Sql


def create_brainbox_service_and_api():
    services = {
        'OpenTTS': OpenTTS(OpenTTSSettings()),
    }
    cache_path = Loc.data_folder / 'demo/brainbox/cache'
    service = BrainBoxService(services, AlwaysOnPlanner(), cache_path)
    comm = Sql.file(Loc.data_folder / 'demo/brainbox/brainbox.db')
    server = BrainBoxWebServer(
        BrainBox().settings.brain_box_web_port,
        comm,
        cache_path,
        service
    )
    return server, BrainBox().create_api('127.0.0.1')
