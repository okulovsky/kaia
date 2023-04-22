"""
And another way is to simply combine `Authorization` routine with echo routine we have written before.
This way we will completely avoid copy-paste.
"""
from demos.eaglesong.common import *
from kaia.eaglesong.amenities.authorization import Authorization
from demos.eaglesong.example_01_echobot import main as echobot_main


bot = Bot("auth3", factory = lambda: Authorization(echobot_main))


if __name__ == '__main__':
    run(bot)
