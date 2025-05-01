import sys

from kaia.demo import *
from kaia.common import Loc


mic_settings = MicSettings(
    mic_device_index=-1,
    sample_rate=16000,
    silence_level=2000
)


if __name__ == '__main__':
    kaia_session_id = None

    if (len(sys.argv) > 1):
        print("Custom kaia session id: " + sys.argv[1])
        kaia_session_id = sys.argv[1]

    app = KaiaApp(folder=Loc.data_folder/'demo', session_id=kaia_session_id)

    set_brainbox_service_and_api(app)
    set_streaming_service_and_api_address(app)
    set_avatar_service_and_api(app)
    set_web_service_and_api(app)
    set_audio_control_service_and_api(app, mic_settings)
    set_core_service(app)

    fork_app = app.get_fork_app()
    fork_app.run()


