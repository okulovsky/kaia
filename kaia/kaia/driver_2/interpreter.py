from typing import *
from ...eaglesong.core import IAutomaton, Interpreter, primitives as prim
from ..server_2 import Message, KaiaApi
from ..core import KaiaMessage

class Confirmation:
    pass

class KaiaInterpreter(Interpreter):
    def __init__(self,
                 automaton: IAutomaton,
                 kaia_api: KaiaApi
                 ):
        self.kaia_api = kaia_api
        super().__init__(automaton)
        self.handle_type(prim.Return, self._process_return)
        self.handle_type(prim.Listen, self._process_listen)
        self.handle_type(prim.Terminate, self._process_terminate)
        self.handle_type(prim.Audio, self._process_audio)
        self.handle_type(prim.Image, self._process_image)
        self.handle_type(prim.Empty, self._process_empty)
        self.handle_type(Message, self._publish_message)
        self.handle_type(KaiaMessage, self._publish_message)


    def _process_empty(self, response):
        return Interpreter.continue_cycle()

    def _process_listen(self, response):
        return Interpreter.interrupt_cycle()

    def _process_return(self, response):
        return Interpreter.reset_automaton()

    def _process_terminate(self, response: prim.Terminate):
        self._publish_message(Message(
            Message.Type.Error,
            f'Error when handling the chat:\n\n{response.message}\n\nTo restart the bot, execute /start command or write any message',
            ))
        return Interpreter.reset_automaton()

    def _publish_voice(self, audio: prim.Audio):
        self.kaia_api.add_sound(audio)

    def _publish_message(self, message: Message):
        self.kaia_api.add_message(message)
        return Interpreter.continue_cycle(Confirmation())


    def _process_audio(self, item: prim.Audio):
        if item.text is not None:
            self._publish_message(Message(
                Message.Type.ToUser,
                item.text
            ))
        self._publish_voice(item)
        return Interpreter.continue_cycle(Confirmation())

    def _process_image(self, item: prim.Image):
        self.kaia_api.add_image(item)
        return Interpreter.continue_cycle(Confirmation())

    def process(self, item):
        return self._process(item)