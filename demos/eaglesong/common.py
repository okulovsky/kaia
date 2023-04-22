import os
from kaia.infra import Loc
from kaia.eaglesong.drivers.telegram import TelegramDriver, TelegramTranslationFilter
from kaia.eaglesong.core import *
from telegram.ext import Application
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.CRITICAL)


class Bot:
    def __init__(self,
                 name = None,
                 function = None,
                 factory = None,
                 proc_factory = None,
                 timer=False,
                 timer_function = None,
                 add_telegram_filter = True
                 ):
        self.name = name
        self.function = function
        self.factory = factory
        self.proc_factory = proc_factory
        self.timer_function = timer_function
        self.timer = timer
        self.add_telegram_filter = add_telegram_filter
        self.processor = None


    def _create_routine(self):
        if self.function is not None:
            return Routine.interpretable(self.function, PushdownFilter)
        elif self.factory is not None:
            return self.factory()
        elif self.proc_factory is not None:
            if self.processor is None:
                raise ValueError('`proc_factory` is defined, but `processor` is not set!')
            return self.proc_factory(self.processor)
        raise ValueError("Cannot create routine: no factory is set")


    def create_generic_routine(self):
        if not self.add_telegram_filter:
            raise ValueError('This bot is not generic: `add_telegram_filter` is False, so, it is telegram-native')
        if self.timer_function is not None:
            raise ValueError('This bot is not genetic: `timer_function` is set')
        return self._create_routine()


    def create_telegram_routine(self, chat_id):
        routine = self._create_routine()
        if self.add_telegram_filter:
            routine = TelegramTranslationFilter(routine)
        return routine


    def create_telegram_driver(self, app):
        driver = TelegramDriver(app, self.create_telegram_routine, True)
        if self.timer:
            driver.add_timer('timer', 1, None)
        elif self.timer_function is not None:
            driver.add_timer(
                'timer',
                1,
                lambda: Routine.interpretable(self.timer_function, PushdownFilter, TelegramTranslationFilter)
            )
        return driver





def run(bot: Bot):
    app = Application.builder().token(os.environ['KAIA_TEST_BOT']).build()
    driver = bot.create_telegram_driver(app)
    app.run_polling()
