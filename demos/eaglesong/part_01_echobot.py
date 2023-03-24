from typing import *
from kaia.eaglesong.telegram import TgCommand, TgUpdate
from kaia.eaglesong.arch import  Listen
from demos.eaglesong.common import *

def echo(context: Callable[[], TgUpdate]):
    yield TgCommand.mock().send_message(
        chat_id = context().chat_id,
        text=f'Hi {context().update.message.from_user.name}! Say anything and I will repeat.'
    )
    while True:
        yield Listen()
        input_text = context().update.message.text
        yield TgCommand.mock().send_message(context().chat_id, input_text)

run(echo)