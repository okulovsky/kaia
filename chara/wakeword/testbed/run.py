import webbrowser
from pathlib import Path
from loguru import logger
from avatar.app import AvatarApi, AvatarServer, AvatarServerSettings, compile_frontend
from avatar.daemon.common.known_messages import WakeWordEvent
from foundation_kaia.marshalling import TestApi
from foundation_kaia.misc import Loc

# The model is selected in index.html. The .onnx heads go to testbed/resources/WakeWordModels
# (git-ignored), with the same layout as kaia/app/files/avatar-resources/WakeWordModels.
PORT = 13002

FOLDER = Path(__file__).parent


if __name__ == '__main__':
    frontend_folder = Loc.data_folder / 'wakeword_testbed' / 'frontend'
    compile_frontend(frontend_folder)

    settings = AvatarServerSettings(
        port=PORT,
        custom_html=(FOLDER / 'index.html').read_text(),
        frontend_folder=frontend_folder,
        resources_folder=FOLDER / 'resources',
        aliases_discovery_namespaces=('avatar',),
    )

    with TestApi(AvatarApi, AvatarServer(settings)) as api:
        client = api.create_client()
        webbrowser.open(api.base_url)
        for message in client.query():
            if isinstance(message, WakeWordEvent):
                logger.info(f"Wake word: {message.word}")
