"""
This functionality is so useful that it's implemented in `kaia.eaglesong.amenities`: a (yet) small set
of handy routines.
"""
from demos.eaglesong.common import *
from kaia.eaglesong.amenities.authorization import Authorization


def main(context: BotContext):
    yield Authorization()
    yield f'Hello. Your user_id is {context.user_id}. Say anything and I will repeat. Or /start to reset.'
    while True:
        yield Listen()
        yield context.input


bot = Bot("auth2", main)

if __name__ == '__main__':
    run(bot)
