from kaia.brainbox import (
    BrainBoxWebServer, BrainBoxService, BrainBox
)
from kaia.brainbox.core.planers import AlwaysOnPlanner
from kaia.brainbox.deciders import (
    OpenTTSInstaller, OpenTTSSettings, RhasspyKaldiInstaller, RhasspyKaldiSettings,
    WhisperInstaller, WhisperSettings, ResemblyzerInstaller, ResemblyzerSettings,
    Collector
)
from kaia.infra import Loc, Sql


def create_brainbox_service_and_api(services = None, folder = 'demo/brainbox'):
    if services is None:
        services = {
            'OpenTTS': OpenTTSInstaller(OpenTTSSettings()),
            'Whisper': WhisperInstaller(WhisperSettings()),
            'RhasspyKaldi': RhasspyKaldiInstaller(RhasspyKaldiSettings()),
            'Collector': Collector(),
            'Resemblyzer': ResemblyzerInstaller(ResemblyzerSettings())
        }
    cache_path = Loc.data_folder / folder/ f'cache'
    service = BrainBoxService(services, AlwaysOnPlanner(), cache_path)
    comm = Sql.file(Loc.data_folder / folder / 'brainbox.db')
    server = BrainBoxWebServer(
        BrainBox().settings.brain_box_web_port,
        comm,
        cache_path,
        service
    )
    return server, BrainBox().create_api('127.0.0.1'), cache_path
