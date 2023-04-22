"""
The most important thing to remember is that every time you want your bot
to say or to do something, you have to type `yield`.

The same applies when you want your bot to listen: you type `yield Listen()`.

With this, the following code is pretty self-explainatory: say the welcome message,
and then listen to what the user says and then repeat to him.

Class `Bot`, imported from `kaia.eaglesong.core` is specific for demos,
and incapsulates different ways of defining the bots. We will cover these ways
along the demo, right now it's simple: just bot over `main` function. `run` starts
this bot.

"""

from kaia.eaglesong.core import BotContext, Listen
from demos.eaglesong.common import Bot, run


def main(context: BotContext):
    yield f'Hello. Your user_id is {context.user_id}. Say anything and I will repeat. Or /start to reset.'
    while True:
        yield Listen()
        yield context.input


bot = Bot("echobot", main)


if __name__ == '__main__':
    run(bot)
