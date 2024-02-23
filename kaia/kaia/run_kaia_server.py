from kaia.kaia.core import KaiaWebServer, KaiaApi, KaiaMessage
from pathlib import Path

if __name__ == '__main__':
    def updates(api: KaiaApi):
        yield api.add_message(KaiaMessage(True, 'Hey'))
        yield api.add_message(KaiaMessage(False, 'Hello there'))
        with open(Path(__file__).parent/'gui/example.png','rb') as file:
            bytes = file.read()
        yield api.set_image(bytes)
        yield api.add_message(KaiaMessage(True, 'How are you doing'))
        yield api.add_message(KaiaMessage(False, 'Doing just fine, thank you'))

    gui_folder = Path(__file__).parent/'gui'
    KaiaWebServer.debug_kaia_server(
        gui_folder/'index.html',
        gui_folder/'static',
        updates,
        cmd_prefix="firefox",
        stay_after_commands=True
    )







