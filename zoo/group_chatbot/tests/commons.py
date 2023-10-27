from unittest import TestCase
from kaia.eaglesong.drivers.telegram import TelegramScenario as S, TgContext, TelegramSimplifier
from kaia.eaglesong.core import Return, Automaton

from string import Template
from datetime import datetime
import telegram as tg

def Test(skill):
    return S(lambda: Automaton( TelegramSimplifier(skill.run).run, TgContext(None, 123)))