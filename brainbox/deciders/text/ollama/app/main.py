import subprocess
import sys
import threading

from foundation_kaia.marshalling import Server, ServiceComponent, ApiUtils
from foundation_kaia.brainbox_utils import ModelInstallingSupport, InstallingSupport
from model import OllamaInstaller
from service import OllamaService

OLLAMA_BINARY = '/bin/ollama'
OLLAMA_PORT = 11434
BRAINBOX_PORT = 8080


def _forward(stream, dest):
    for line in stream:
        dest.buffer.write(line)
        dest.buffer.flush()


def _start_ollama_serve():
    proc = subprocess.Popen(
        [OLLAMA_BINARY, 'serve'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    threading.Thread(target=_forward, args=(proc.stdout, sys.stdout), daemon=True).start()
    threading.Thread(target=_forward, args=(proc.stderr, sys.stderr), daemon=True).start()
    return proc


if __name__ == '__main__':
    model = sys.argv[1] if len(sys.argv) > 1 else None
    _start_ollama_serve()
    ApiUtils.wait_for_reply(f'http://127.0.0.1:{OLLAMA_PORT}/', 60)
    installer = OllamaInstaller()
    server = Server(
        BRAINBOX_PORT,
        ServiceComponent(OllamaService(model)),
        ServiceComponent(InstallingSupport(installer)),
        ServiceComponent(ModelInstallingSupport[str](installer)),
    )
    server.create_web_app_entry_point().run()
