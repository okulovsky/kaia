from kaia.persona.sandbox import create_sandbox_assistant
from pathlib import Path
from kaia.infra import Loc
from kaia.persona.dub.core import DubbingPack, RhasspyAPI
from kaia.persona.dialogue import UtterancesTranslator
from kaia.eaglesong.drivers.telegram import TelegramDriver, TelegramTranslator
from kaia.eaglesong.core import Automaton
import os
from telegram.ext import Application

if __name__ == '__main__':
    files_folder = Path(__file__).parent/'files'
    base_pack_path =  files_folder/'intent_dubbing.zip'
    assistant_pack_path =  files_folder/'assistant_dubbing.zip'
    base_host_path =  Loc.temp_folder/'demos/dubbing/intent_dubbing'
    assistant_host_path =  Loc.temp_folder/'demos/dubbing/assistant_dubbing'

    ha = create_sandbox_assistant()
    pack = DubbingPack.from_zip(base_host_path, base_pack_path, assistant_pack_path)
    rhasspy_api = RhasspyAPI.create('http://127.0.0.1:12101', ha.get_intents())
    rhasspy_api.train()

    bot_factory = lambda context: Automaton(
        TelegramTranslator(
            UtterancesTranslator(
                create_sandbox_assistant(), rhasspy_api, pack.create_dubber())),
        context
    )


    app = Application.builder().token(os.environ['KAIA_TEST_BOT']).build()
    driver = TelegramDriver(app, bot_factory)
    app.run_polling()



