import os
import time
import webbrowser

from avatar.server import AvatarServer, AvatarApi, AvatarStream, AvatarServerSettings, MessagingComponent
from phonix.components import PhonixMonitoringComponent, PhonixRecordingComponent, PhonixApi
from phonix.daemon import *
from avatar.messaging import TestStream
from foundation_kaia.fork import Fork
from foundation_kaia.misc import Loc

if __name__ == '__main__':
    port = 13002
    api = AvatarApi(f'127.0.0.1:{port}')
    stream = AvatarStream(api)
    recording_api = PhonixApi(f'127.0.0.1:{port}')
    SILENCE_MARGIN = 1.0
    daemon = PhonixDeamon(
        stream.create_client(),
        AvatarFileRetriever(api),
        PyAudioInput(),
        PyAudioOutput(),
        [
            PorcupineWakeWordUnit(),
            SilenceMarginUnit(0.02, SILENCE_MARGIN),
            RecordingUnit(recording_api, 1.1*SILENCE_MARGIN),
            TooLongOpenMicUnit(15),
            LevelReportingUnit()
        ],
        PhonixDeamon.get_default_system_sounds()
    )
    daemon.run_in_thread()
    folder = Loc.temp_folder/'phonix/recordings'
    recording = PhonixRecordingComponent(folder)
    monitoring = PhonixMonitoringComponent(folder)
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
        port,
    )

    with Fork(AvatarServer(settings)):
        api.wait()
        webbrowser.open(f'http://127.0.0.1:{settings.port}/phonix-monitor')
        time.sleep(100000)
