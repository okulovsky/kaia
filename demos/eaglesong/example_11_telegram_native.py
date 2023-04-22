"""
`eaglesong` allows you to write the skills for Telegram only,
without using TelegramTranslationFilter.

In this case, `TgContext` will be your context (containing Telegram primitives
of the input), and the output will be TgCommand. To create TgCommand with
hints from IDE, use TgCommand.mock().

The general recommendation though is to avoid this: there is no reason
to make your chat flows only compatible with Telegram. Also, the testing
of this scenario is a nightmare (you can check the corresponding unit tests
to have a taste).
"""

from demos.eaglesong.common import *
from kaia.eaglesong.drivers.telegram import TgCommand, TgContext

def main(context: TgContext):
    username = context.update.message.chat.username
    yield  TgCommand.mock().send_message(
        chat_id = context.chat_id,
        text = f'Hello, {username}. Say anything and I will repeat. Or /start to reset.'
    )
    while True:
        yield Listen()
        message_text = context.update.message.text
        yield TgCommand.mock().send_message(chat_id=context.chat_id, text=message_text)


bot = Bot("telegram", main, add_telegram_filter=False)


if __name__ == '__main__':
    run(bot)