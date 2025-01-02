from typing import *
from ...core import IAutomaton
from .telegram_driver import TelegramDriver
from telegram.ext import Application


class TelegramService:
    def __init__(self,
                 automaton_factory: Callable[[], IAutomaton],
                 bot_key: str,
                 ):
        self.automaton_factory = automaton_factory
        self.bot_key = bot_key

    def __call__(self):
        app = Application.builder().token(self.bot_key).build()
        driver = TelegramDriver(app, self.automaton_factory)
        app.run_polling()





