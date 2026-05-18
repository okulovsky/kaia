import subprocess
import sys
import threading
from pathlib import Path

from foundation_kaia.marshalling import Server, ServiceComponent, ApiUtils
from foundation_kaia.brainbox_utils.models import ModelInstallingSupport, InstallingSupport

from model import ComfyUIInstaller, ComfyUIInstallation
from service import ComfyUIService

COMFYUI_MAIN = Path('/home/app/comfy/ComfyUI/main.py')
COMFYUI_PORT = 8188
BRAINBOX_PORT = 8080


def _forward(stream, dest):
    for line in stream:
        dest.buffer.write(line)
        dest.buffer.flush()


if __name__ == '__main__':
    comfyui = subprocess.Popen(
        [sys.executable, str(COMFYUI_MAIN),
         '--enable-manager', '--listen', '0.0.0.0', '--port', str(COMFYUI_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    threading.Thread(target=_forward, args=(comfyui.stdout, sys.stdout), daemon=True).start()
    threading.Thread(target=_forward, args=(comfyui.stderr, sys.stderr), daemon=True).start()

    ApiUtils.wait_for_reply(f"http://127.0.0.1:{COMFYUI_PORT}/", 30)

    installer = ComfyUIInstaller()

    server = Server(
        BRAINBOX_PORT,
        ServiceComponent(ComfyUIService()),
        ServiceComponent(InstallingSupport(installer)),
        ServiceComponent(ModelInstallingSupport[ComfyUIInstallation](installer)),
    )
    server.create_web_app_entry_point().run()
