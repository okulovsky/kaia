from typing import *
from ...eaglesong.core import IAutomaton, Interpreter, primitives as prim
from ...avatar.dub.core import RhasspyAPI
from .kaia_message import KaiaMessage
from .kaia_server import KaiaApi







class KaiaInterpreter(Interpreter):
    def __init__(self,
                 automaton: IAutomaton,
                 rhasspy_api: RhasspyAPI,
                 kaia_api: Optional[KaiaApi] = None
                 ):
        self.rhasspy_url = rhasspy_api
        self.kaia_api = kaia_api
        super().__init__(automaton)
        self.handle_type(prim.Return, self._process_return)
        self.handle_type(prim.Listen, self._process_listen)
        self.handle_type(prim.Terminate, self._process_terminate)
        self.handle_type(prim.Audio, self._process_audio)
        self.handle_type(KaiaMessage, self._publish_message)
        self.handle_type(prim.Image, self._process_image)
        self.handle_type(str, self._process_str)

    def _process_listen(self, response):
        return Interpreter.interrupt_cycle()

    def _process_return(self, response):
        return Interpreter.reset_automaton()

    def _process_terminate(self, response: prim.Terminate):
        self._publish_message(KaiaMessage(
            True,
            f'Error when handling the chat:\n\n{response.message}\n\nTo restart the bot, execute /start command or write any message',
            True))
        return Interpreter.reset_automaton()

    def _publish_voice(self, audio: prim.Audio):
        self.rhasspy_url.play_wav(audio.data)

    def _publish_message(self, message: KaiaMessage):
        if self.kaia_api is not None:
            self.kaia_api.add_message(message)
        return Interpreter.continue_cycle()


    def _process_audio(self, item: prim.Audio):
        if item.text is not None:
            self._publish_message(KaiaMessage(
                True,
                item.text
            ))
        self._publish_voice(item)
        return Interpreter.continue_cycle()

    def _process_image(self, item: prim.Image):
        self.kaia_api.set_image(item.data)
        return Interpreter.continue_cycle()

    def _process_str(self, item: str):
        self._publish_message(KaiaMessage(True, item))
        return Interpreter.continue_cycle()

    def process(self, item):
        return self._process(item)