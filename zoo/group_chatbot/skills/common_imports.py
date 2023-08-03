from typing import *
from kaia.eaglesong.core import Return, RoutineBase, Automaton, Routine
from kaia.eaglesong.drivers.telegram import TgCommand, TgContext
import telegram as tg
import logging
from string import Template
logger = logging.getLogger('group_chat')