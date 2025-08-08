import os

from avatar.server import AvatarServer, AvatarApi, AvatarStream, AvatarServerSettings, MessagingComponent
from phonix.components import PhonixMonitoringComponent, PhonixRecordingComponent, PhonixApi
from phonix.daemon import *
from avatar.messaging import TestStream
from foundation_kaia.fork import Fork
from foundation_kaia.misc import Loc

if __name__ == '__main__':
    port = 13000
    api = AvatarApi(f'127.0.0.1:{port}')
    stream = AvatarStream(api)
    recording_api = PhonixApi(f'127.0.0.1:{port}')

    daemon = PhonixDeamon(
        stream.create_client(),
        AvatarFileRetriever(api),
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
    daemon.run_in_thread()
    recording = PhonixRecordingComponent(Loc.temp_folder/'phonix/recordings')
    monitoring = PhonixMonitoringComponent()
    db_path = Loc.test_folder/'phonix/db'
    if db_path.is_file():
        os.unlink(db_path)
    messaging = MessagingComponent(db_path)

    settings = AvatarServerSettings(
        (
            recording,
            monitoring,
            messaging
        ),
        port
    )
    AvatarServer(settings)()
