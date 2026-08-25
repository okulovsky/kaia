import argparse
import socket
import time
import webbrowser
from pathlib import Path

from avatar.app import AvatarApi, AvatarServer, AvatarServerSettings
from avatar.app.scripts.scripts_compilation import compile as compile_scripts
from avatar.messaging import AvatarDaemon, BindingSettings
from chara.common.llm import BrainBoxLLMEngine, LLMSetup
from foundation_kaia.fork import Fork
from foundation_kaia.misc import Loc

from creative_articulator.drama.demo.characters import CHARACTERS, DEFAULT_PROTAGONIST, get_character
from creative_articulator.drama.demo.story import build_story
from creative_articulator.drama.driver import ChatService, ErrorLogger, StoryDriver

PORT = 14000
MODEL = 'gemma3:27b-it-q4_K_M'
WEB_FOLDER = Path(__file__).parent / 'web'
FRONTEND_FOLDER = WEB_FOLDER / 'frontend'
TEMP_FOLDER = Path(__file__).parent / 'temp'
SAVE_FILE = TEMP_FOLDER / 'story.pkl'
ALIASES_NAMESPACES = ('avatar.daemon', 'creative_articulator.drama.driver')


def check_port_is_free(port: int):
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(('0.0.0.0', port))
        except OSError as ex:
            raise RuntimeError(
                f'Port {port} is already taken by another process, run with --port to choose a free one'
            ) from ex


def run(character: str, model: str = MODEL, port: int = PORT, reset: bool = False, debug_llm: bool = False):
    protagonist = get_character(character)
    check_port_is_free(port)

    TEMP_FOLDER.mkdir(parents=True, exist_ok=True)
    if reset and SAVE_FILE.is_file():
        SAVE_FILE.unlink()

    compile_scripts(Loc.root_folder / 'avatar' / 'web' / 'src', FRONTEND_FOLDER / 'scripts')

    server = AvatarServer(AvatarServerSettings(
        port=port,
        web_folder=WEB_FOLDER,
        frontend_folder=FRONTEND_FOLDER,
        aliases_discovery_namespaces=ALIASES_NAMESPACES,
    ))

    with Fork(server):
        api = AvatarApi(f'http://127.0.0.1:{port}')
        api.wait_for_connection(20)

        llm = LLMSetup(BrainBoxLLMEngine(), model)
        if debug_llm:
            llm = llm.debug()

        driver = StoryDriver(build_story(protagonist, llm))

        client = api.create_client()
        daemon = AvatarDaemon(client, add_error_events=True, timeout_in_pull_in_seconds=0.1)
        daemon.rules.bind(
            ChatService(driver, SAVE_FILE, protagonist.name),
            BindingSettings().asynchronous(),
        )
        daemon.rules.bind(ErrorLogger())
        daemon.run_in_thread()

        time.sleep(1)
        print(f'Playing as {protagonist.name}. Open http://127.0.0.1:{port}/ to chat, Ctrl+C to stop.')
        if 'web' not in api.messages.get_active_clients():
            webbrowser.open(f'http://127.0.0.1:{port}/')

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass


def main():
    parser = argparse.ArgumentParser(description='Chat in Prostokvashino as one of the three characters.')
    parser.add_argument('character', nargs='?', default=DEFAULT_PROTAGONIST.name,
                        choices=[c.name for c in CHARACTERS],
                        help='the character the human plays')
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--reset', action='store_true', help='discard the saved story and start over')
    parser.add_argument('--debug-llm', action='store_true', help='print the prompts and the answers')
    args = parser.parse_args()
    run(args.character, args.model, args.port, args.reset, args.debug_llm)


if __name__ == '__main__':
    main()
