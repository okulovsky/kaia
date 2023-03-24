import os
from kaia.eaglesong.telegram import TelegramBridge
from kaia.eaglesong.arch import PushdownAutomaton, FunctionalSubroutine
from telegram.ext import Application
from kaia.infra import Loc
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def run(root):
    app = Application.builder().token(os.environ['KAIA_TEST_BOT']).build()
    bridge = TelegramBridge(app, lambda _: PushdownAutomaton(FunctionalSubroutine(root)), True)
    app.run_polling()
