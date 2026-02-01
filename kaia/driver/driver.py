from typing import Type
import time
from typing import Callable, Any
from avatar.messaging import StreamClient
from avatar.daemon import TextCommand, STTService, TickEvent, SoundCommand
from loguru import logger
from ..assistant import KaiaContext
from eaglesong import Automaton
from .interpreter import KaiaInterpreter
import traceback
from avatar.daemon import ChatCommand, InitializationEvent
from threading import Thread
from ..assistant import KaiaAssistant
from abc import ABC, abstractmethod

class IAssistantFactory(ABC):
    @abstractmethod
    def create_assistant(self, context: KaiaContext) -> Any:
        pass

    @abstractmethod
    def wrap_assistant(self, assistant: Any) -> Any:
        pass


class DefaultAssistantFactory(IAssistantFactory):
    def __init__(self, callable: Callable[[KaiaContext], Any]):
        self.callable = callable

    def create_assistant(self, context: KaiaContext) -> Any:
        return self.callable(context)

    def wrap_assistant(self, assistant: Any) -> Any:
        return assistant




class KaiaDriver:
    def __init__(self,
                 assistant_factory: IAssistantFactory,
                 client: StreamClient,
                 expect_confirmations_for_types: tuple[Type,...] = (TextCommand, SoundCommand),
                 context_setup: Callable[[KaiaContext], None] = None,
                 ):
        self.assistant_factory = assistant_factory
        self.client = client
        self.expect_confirmations_for_types = expect_confirmations_for_types
        self.interpreter: KaiaInterpreter|None = None
        self.rhasspy_training_is_done: bool = False
        self.context_setup = context_setup


    def initialize(self):
        context = KaiaContext(self.client)
        if self.context_setup is not None:
            self.context_setup(context)
        assistant = self.assistant_factory.create_assistant(context)

        if not isinstance(assistant, KaiaAssistant):
            logger.info("The assistant is not KaiaAssistant, skipping training")
        else:
            if not self.rhasspy_training_is_done:
                logger.info("Sending Rhasspy Train Command")
                packs = assistant.get_intents()
                context.get_client().put(STTService.RhasspyTrainingCommand(packs))

        assistant = self.assistant_factory.wrap_assistant(assistant)
        automaton = Automaton(assistant, context)
        self.interpreter = KaiaInterpreter(self.client, automaton, self.expect_confirmations_for_types)
        logger.info("Interpreter (re)created")


    def _trim(self, obj):
        return str(obj)[:100]

    def process(self, message):
        if self.interpreter is None:
            logger.info("Interpreter is not created, creating")
            self.initialize()
        elif isinstance(message, InitializationEvent):
            logger.info("Interpreter recreation is requested, creating")
            self.initialize()

        try:
            logger.info(f"Item to interpreter: {self._trim(message)}")
            self.interpreter.process(message)
        except:
            err = traceback.format_exc()
            self.client.put(ChatCommand(err, ChatCommand.MessageType.error))
            self.interpreter = None
            logger.error(f'Error occured, interpreter is nullified:\n{err}')

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