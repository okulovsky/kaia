from dataclasses import dataclass
from .app import KaiaApp, IAppInitializer
from phonix import daemon as d
from avatar.messaging import TestStream

@dataclass
class PhonixAppSettings(IAppInitializer):
    device: int = -1
    rate: int = 16000
    chunk: int = 512
    channels: int = 1
    silence_level: float = 0.03
    silence_margin_length_in_seconds: float = 1
    max_open_mic_time_in_seconds: float = 15
    in_unit_test_environment: bool = False
    supress_reports: bool = False
    async_messaging: bool = False

    def bind_app(self, app: 'KaiaApp'):
        if self.in_unit_test_environment:
            input = d.FakeInput()
            output = d.FakeOutput()
        else:
            input = d.PyAudioInput(self.device, self.rate, self.chunk, self.channels)
            output = d.PyAudioOutput()

        units = [
            d.PorcupineWakeWordUnit(),
            d.SilenceMarginUnit(
                self.silence_level,
                self.silence_margin_length_in_seconds,
                1 if not self.supress_reports else None
            ),
            d.RecordingUnit(
                app.phonix_api,
                self.silence_margin_length_in_seconds * 1.1
            ),
            d.TooLongOpenMicUnit(self.max_open_mic_time_in_seconds)
        ]

        if self.in_unit_test_environment:
            units.append(d.MicRecordingUnit(app.working_folder/'mic_recording.wav'))

        if not self.supress_reports:
            units.append(d.LevelReportingUnit())

        daemon = d.PhonixDeamon(
            app.create_avatar_client(),
            d.AvatarFileRetriever(app.avatar_api),
            input,
            output,
            units,
            d.PhonixDeamon.get_default_system_sounds() if not self.in_unit_test_environment else {},
            async_messaging=self.async_messaging
        )

        app.phonix_daemon = daemon


