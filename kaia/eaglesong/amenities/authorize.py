from typing import *
from ..arch import *
from ..telegram import TgUpdate, TgCommand
from yo_fluq_ds import *
from pathlib import Path

class Authorization(Subroutine):
    def __init__(self, pin, auth_file_location):
        self.pin = pin
        self.auth_file_location = Path(auth_file_location)

    def run(self, c: Callable[[],TgUpdate]):
        if not self.auth_file_location.is_file():
            yield TgCommand.mock().send_message(c().chat_id, 'Enter pin to authorize')
            yield Listen()
            pin = c().update.message.text
            if self.pin != pin:
                yield TgCommand.mock().send_message(c().chat_id, 'Pin is incorrect')
                yield Terminate('Unauthorized')
            FileIO.write_text(str(c().chat_id), self.auth_file_location)
            yield TgCommand.mock().send_message(c().chat_id, "Authorized")
            yield Return()
        else:
            chat_id = int(FileIO.read_text(self.auth_file_location))
            if c().chat_id!=chat_id:
                yield Terminate('Unauthorized')
            else:
                yield Return()




