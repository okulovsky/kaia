import os
from kaia.eaglesong.telegram import TelegramBridge
from kaia.eaglesong.arch import PushdownAutomaton, FunctionalSubroutine
from telegram.ext import Application
from kaia.infra import Loc
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def run(root):
    app = Application.builder().token(os.environ['KAIA_TEST_BOT']).build()
    bridge = TelegramBridge(app, lambda _: PushdownAutomaton(FunctionalSubroutine.ensure(root)), True)
    app.run_polling()


def run_with_timer(root, timer):
    app = Application.builder().token(os.environ['KAIA_TEST_BOT']).build()
    bridge = TelegramBridge(app, lambda _: PushdownAutomaton(FunctionalSubroutine.ensure(root)), True)
    bridge.add_timer('timer', 1, timer)
    app.run_polling()