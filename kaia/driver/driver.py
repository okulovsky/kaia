from typing import Type
import time
from typing import Callable, Any
from avatar.messaging import StreamClient
from avatar.services import UtteranceSequenceCommand, TextCommand
from loguru import logger
from .context import KaiaContext
from eaglesong import Automaton
from .interpreter import KaiaInterpreter
from .input_transformer import IKaiaInputTransformer
import traceback
from avatar.services import ChatCommand, InitializationEvent
from threading import Thread
from ..assistant import KaiaAssistant


class KaiaDriver:
    def __init__(self,
                 assistant_factory: Callable[[KaiaContext],Any],
                 client: StreamClient,
                 input_transformer: IKaiaInputTransformer|None = None,
                 expect_confirmations_for_types: tuple[Type,...] = (UtteranceSequenceCommand, TextCommand)
                 ):
        self.assistant_factory = assistant_factory
        self.client = client
        self.input_transformer = input_transformer
        self.expect_confirmations_for_types = expect_confirmations_for_types
        self.interpreter: KaiaInterpreter|None = None

    def initialize(self):
        context = KaiaContext(self.client)
        assistant = self.assistant_factory(context)

        automaton = Automaton(assistant, context)
        self.interpreter = KaiaInterpreter(self.client, automaton, self.expect_confirmations_for_types)
        logger.info("Interpreter (re)created")




    def _trim(self, obj):
        return str(obj)[:100]

    def process(self, message):
        logger.info(f"Processing message {self._trim(message)}")

        if self.interpreter is None:
            logger.info("Interpreter is not created, creating")
            self.initialize()
        elif isinstance(message, InitializationEvent):
            logger.info("Interpreter recreation is requested, creating")
            self.initialize()

        if self.input_transformer is not None:
            item = self.input_transformer.transform(message)
            if item is None:
                return
        else:
            item = message
        try:
            logger.info(f"Item to interpreter: {self._trim(item)}")
            self.interpreter.process(message, item)
        except:
            err = traceback.format_exc()
            self.client.put(ChatCommand(err, ChatCommand.MessageType.error))
            self.interpreter = None
            logger.error(f'Error occured, interpreted is nullified:\n{err}')

        if self.interpreter is not None and self.interpreter.has_exited():
            logger.info("Automaton has exited, re-initizalizing")
            self.initialize()

    def run(self):
        self.client.initialize()
        while True:
            messages = self.client.pull()
            for message in messages:
                self.process(message)
            if len(messages) == 0:
                time.sleep(0.1)

    def __call__(self):
        self.run()

    def run_in_thread(self):
        Thread(target=self.run, daemon=True).start()