import shutil
import time
from kaia.kaia.server.bus import Bus
from kaia.kaia.audio_control.wav_streaming import WavStreamingTestApi, WavApiSettings, WavServerSettings
from demos.kaia.audio_control import create_release_control_settings
from kaia.infra.app import KaiaApp
from kaia.kaia.server.api import KaiaApi, KaiaServerSettings, Message, KaiaServer
from kaia.infra import Loc
from pathlib import Path

def run_test_3():
    apis: dict[str, KaiaApi] = dict()
    cache = Loc.temp_folder/'kaia_server_test_3_file_cache'
    shutil.rmtree(cache, ignore_errors=True)
    shutil.copytree(Path(__file__).parent / 'files/cache', cache)

    with Loc.create_temp_file('kaia_server_test_3', 'db') as db_path:
        app = KaiaApp()
        settings = KaiaServerSettings(
            db_path,
            file_cache_folder=cache,
            additional_static_folders=dict(alt=Path(__file__).parent / 'test_1/files/alternative_static')
        )

        service = KaiaServer(settings)
        app.add_subproc_service(service)
        app.run_services_only()

        with WavStreamingTestApi(WavApiSettings(), WavServerSettings(cache)):

            bus = Bus(db_path)
            while True:
                for session in bus.get_sessions():
                    if session not in apis:
                        api = KaiaApi(bus, session)
                        api.add_message(Message(Message.Type.ToUser, "Hey!"))
                        api.add_message(Message(Message.Type.FromUser, "Hello!", avatar='/alt/lina.png'))
                        api.add_image('img1.png')
                        api.add_sound('sound1.mpeg')
                        apis[session] = api
                    else:
                        api = apis[session]

                    updates = api.pull_updates()
                    for update in updates:
                        if update.type == 'audio_command':
                            api.add_message(Message(Message.Type.ToUser, 'Message received'))
                            api.add_sound(update.payload['filename'])
                            break

                time.sleep(0.1)


if __name__ == '__main__':
    run_test_3()