import time
import webbrowser
from foundation_kaia.fork import Fork
from phonix.app import PhonixAppSettings

if __name__ == '__main__':
    settings = PhonixAppSettings()
    settings.silent = False
    api = settings.create_avatar_api()
    daemon = settings.create_daemon()
    server = settings.create_debug_avatar_server()

    daemon.run_in_thread()
    with Fork(server):
        api.wait()
        webbrowser.open(f'http://127.0.0.1:{settings.avatar_port}/phonix-monitor')
        time.sleep(100000)
