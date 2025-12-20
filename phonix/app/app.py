import os
from avatar.server import AvatarServer, AvatarApi, AvatarStream, AvatarServerSettings, MessagingComponent
from phonix.components import PhonixMonitoringComponent, PhonixRecordingComponent, PhonixApi
from phonix.daemon import *
from foundation_kaia.misc import Loc
from dataclasses import dataclass

@dataclass
class PhonixAppSettings:
    silence_level: float = 0.02
    avatar_ip_address: str = '127.0.0.1'
    avatar_port: int = 13002
    silence_margin_length: float = 1.0
    silent: bool = True
    tolerate_errors: bool = False
    async_messaging: bool = True
    output_backend: str = 'PyAudio'
    new_porcupine_config: str = ''

    def create_avatar_api(self) -> AvatarApi:
        avatar_address =  f'{self.avatar_ip_address}:{self.avatar_port}'
        api = AvatarApi(avatar_address)
        return api

    def create_daemon(self):
        api = self.create_avatar_api()
        stream = AvatarStream(api)
        client = stream.create_client()
        client.scroll_to_end()
        recording_api = PhonixApi(api.address)
        daemon = PhonixDeamon(
            client,
            AvatarFileRetriever(api),
            PyAudioInput(),
            SoxAudioOutput() if self.output_backend == 'Sox' else PyAudioOutput(),
            [
                (
                    PorcupineWakeWordUnitOldVersion()
                    if (self.new_porcupine_config == '')
                    else PorcupineWakeWordUnitNewVersion(self.new_porcupine_config)
                ),
                SilenceMarginUnit(self.silence_level, self.silence_margin_length),
                RecordingUnit(recording_api, 1.1 * self.silence_margin_length),
                TooLongOpenMicUnit(15),
                LevelReportingUnit()
            ],
            PhonixDeamon.get_default_system_sounds(),
            self.silent,
            self.tolerate_errors,
            self.async_messaging
        )
        return  daemon


    def create_debug_avatar_server(self):
        folder = Loc.temp_folder / 'phonix/recordings'
        recording = PhonixRecordingComponent(folder)
        monitoring = PhonixMonitoringComponent(folder)
        db_path = Loc.test_folder / 'phonix/db'
        if db_path.is_file():
            os.unlink(db_path)
        messaging = MessagingComponent(db_path)

        settings = AvatarServerSettings(
            (
                recording,
                monitoring,
                messaging
            ),
            self.avatar_port,
        )
        return AvatarServer(settings)


