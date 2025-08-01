from dataclasses import dataclass
from .app import KaiaApp, IAppInitializer
from phonix import daemon as d
from phonix.server import PhonixServer
from avatar.messaging import TestStream

@dataclass
class PhonixAppSettings(IAppInitializer):
    device: int = -1
    rate: int = 16000
    chunk: int = 512
    channels: int = 1
    silence_level: float = 0.1
    silence_margin_length_in_seconds: float = 1
    max_open_mic_time_in_seconds: float = 15

    def bind_app(self, app: 'KaiaApp'):
        api = d.RecordingApi(app.avatar_api.address)
        internal_stream = TestStream(10000)

        daemon = d.PhonixDeamon(
            internal_stream.create_client(),
            d.AvatarFileRetriever(app.avatar_api),
            d.PyAudioInput(self.device, self.rate, self.chunk, self.channels),
            d.PyAudioOutput(),
            [
                d.PorcupineWakeWordUnit(),
                d.SilenceMarginUnit(
                    self.silence_level,
                    self.silence_margin_length_in_seconds,
                ),
                d.RecordingUnit(
                    api,
                    self.silence_margin_length_in_seconds*1.1
                ),
                d.LevelReportingUnit(),
                d.TooLongOpenMicUnit(self.max_open_mic_time_in_seconds)
            ],
            d.PhonixDeamon.get_default_system_sounds(),
            app.avatar_stream.create_client(),
        )

        server = PhonixServer(daemon, api)
        app.phonix_server = server


