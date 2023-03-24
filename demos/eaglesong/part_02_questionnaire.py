from typing import *
from kaia.eaglesong.telegram import TgCommand, TgUpdate
from kaia.eaglesong.arch import  Listen, Return
from demos.eaglesong.common import *

def questionnaire(c: Callable[[], TgUpdate]):
    yield TgCommand.mock().send_message(c().chat_id, 'What is your name?')
    yield Listen()
    name = c().update.message.text

    yield TgCommand.mock().send_message(c().chat_id, f'Where are you from, {name}?')
    yield Listen()
    country = c().update.message.text

    yield Return(name, country)

def main(c: Callable[[], TgUpdate]):
    subroutine = FunctionalSubroutine(questionnaire)
    yield subroutine
    name, country = subroutine.return_value

    yield TgCommand.mock().send_message(c().chat_id, f"Nice to meet you, {name} from {country}!")


run(main)