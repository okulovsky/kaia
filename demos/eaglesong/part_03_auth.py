from typing import *
from kaia.eaglesong.telegram import TgCommand, TgUpdate
from kaia.eaglesong.arch import Listen, Return
from kaia.eaglesong.amenities.authorize import Authorization
from kaia.infra import Loc
from demos.eaglesong.common import *
import os

def main(c: Callable[[], TgUpdate]):
    auth_file = Loc.temp_folder/'auth'
    yield Authorization(os.environ['KAIA_TEST_BOT'][-5:], auth_file)

    yield TgCommand.mock().send_message(
        c().chat_id,
        text=f'Hi {c().update.message.from_user.name}! Say anything and I will repeat. Or use /logout.'
    )

    while True:
        yield Listen()
        input_text = c().update.message.text
        if input_text=='/logout':
            os.remove(auth_file)
            yield TgCommand.mock().send_message(c)
            yield Return()

        yield TgCommand.mock().send_message(c().chat_id, input_text)

run(main)