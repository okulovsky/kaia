from phonix.server import PhonixService
from phonix.recoding_server import RecordingServer, RecordingServerSettings, RecordingApiSettings, RecordingApi
from phonix.daemon import *
from avatar.messaging import TestStream
from foundation_kaia.fork import Fork

if __name__ == '__main__':
    recording_server_settings = RecordingServerSettings()
    recording_server = RecordingServer(recording_server_settings)
    recording_api_settings = RecordingApiSettings()
    recording_api = RecordingApi(recording_api_settings)

    client = TestStream().create_client()
    daemon = PhonixDeamon(
        client,
        FileServerGetter(f'127.0.0.1:{recording_server_settings.port}'),
        PyAudioInput(),
        PyAudioOutput(),
        [
            PorcupineWakeWordUnit(),
            SilenceMarginUnit(0.02, 1),
            RecordingUnit(recording_api, 1.1),
            TooLongOpenMicUnit(15),
            LevelReportingUnit()
        ],
        PhonixDeamon.get_default_system_sounds()
    )

    phonix_service = PhonixService(daemon, recording_api)

    Fork(recording_server).start()
    phonix_service()

