from typing import *
from ..eaglesong.core import Routine
from ..eaglesong.drivers.telegram import TelegramDriver
from telegram.ext import Application
import os


class TelegramService:
    def __init__(self,
                 routine_factory: Callable[[], Routine],
                 bot_key: str,
                 ):
        self.routine_factory = routine_factory
        self.bot_key = bot_key

    def __call__(self):
        app = Application.builder().token(self.bot_key).build()
        driver = TelegramDriver(app, self.routine_factory)
        app.run_polling()





