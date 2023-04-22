from kaia.eaglesong.core import *
from unittest import TestCase
import pandas as pd
from kaia.infra.tasks import SqlSubprocTaskProcessor, SubprocessConfig

def S(bot, proc = None) -> Scenario:
    bot.processor = proc
    return Scenario(lambda: BotContext(123), bot.create_generic_routine(), printing=Scenario.default_printing)


