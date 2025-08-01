from eaglesong.core import IAutomaton, Interpreter, primitives as prim
from avatar.messaging import IMessage, StreamClient
from avatar.services import ChatCommand, UtteranceSequenceCommand
from grammatron import Utterance, UtterancesSequence



class Confirmation:
    pass

class KaiaInterpreter(Interpreter):
    def __init__(self,
                 client: StreamClient,
                 automaton: IAutomaton,
                 ):
        self.client = client
        self.current_message: IMessage|None = None
        super().__init__(automaton)
        self.handle_type(prim.Return, self._process_return)
        self.handle_type(prim.Listen, self._process_listen)
        self.handle_type(prim.Terminate, self._process_terminate)
        self.handle_type(IMessage, self._process_message)
        self.handle_type(str, self._process_str_or_utterance)
        self.handle_type(Utterance, self._process_str_or_utterance)
        self.handle_type(UtterancesSequence, self._process_str_or_utterance)

    def _process_listen(self, response):
        return Interpreter.interrupt_cycle()

    def _process_return(self, response):
        return Interpreter.reset_automaton()

    def _process_message(self, message):
        if self.current_message is not None:
            message = message.as_reply_to(self.current_message)
        self.client.put(message)
        return Interpreter.continue_cycle()

    def _process_terminate(self, response: prim.Terminate):
        self._process_message(ChatCommand(
            f'Error when handling the chat:\n\n{response.message}\n\nTo restart the bot, execute /start command or write any message',
            ChatCommand.MessageType.error
        ))
        return Interpreter.reset_automaton()

    def _process_str_or_utterance(self, message: str|Utterance|UtterancesSequence):
        return self._process_message(UtteranceSequenceCommand(message))

    def process(self, message, item):
        self.current_message = message
        return self._process(item)