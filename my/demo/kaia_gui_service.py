from kaia.kaia.gui import KaiaGuiService, KaiaGuiApi
from pathlib import Path

def create_gui_service_and_api():
    port = 8890
    service = KaiaGuiService(
        KaiaGuiService.get_default_files_folder()/'index.html',
        {
            'static': KaiaGuiService.get_default_files_folder()/'static',
            'additional': Path(__file__).parent/'files/gui'
        },
        port
    )

    api = KaiaGuiApi(f'127.0.0.1:{port}')
    return service, api