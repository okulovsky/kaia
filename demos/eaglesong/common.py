import os
from kaia.infra import Loc
from kaia.eaglesong.drivers.telegram import TelegramDriver, TelegramTranslator
from kaia.eaglesong.core import *
from telegram.ext import Application
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.CRITICAL)


class Bot:
    def __init__(self,
                 name = None,
                 function = None,
                 timer=False,
                 add_telegram_filter = True
                 ):
        self.name = name
        self.function = function
        self.timer = timer
        self.add_telegram_filter = add_telegram_filter
        self.processor = None

    def create_generic_automaton(self, context):
        return Automaton(self.function, context)


    def create_telegram_automaton(self, context):
        routine = self.function
        if self.add_telegram_filter:
            routine = TelegramTranslator(routine).run
        return Automaton(routine, context)


    def create_telegram_driver(self, app):
        driver = TelegramDriver(app, self.create_telegram_automaton)
        if self.timer:
            driver.add_timer('timer', 1, None)
        return driver


def run(bot: Bot):
    app = Application.builder().token(os.environ['KAIA_TEST_BOT']).build()
    driver = bot.create_telegram_driver(app)
    app.run_polling()
