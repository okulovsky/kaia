"""
`eaglesong` allows you to write the skills for Telegram only,
without using TelegramTranslationFilter.

In this case, `TgContext` will be your context (containing Telegram primitives
of the input), and the output will be TgCommand. To create TgCommand with
hints from IDE, use TgCommand.mock().

This is fine approach, if you really want to create a Telegram skill (e.g. one managing Telegram group).
But if you program a generic skill, it is better not to use this approach, as it's better to keep the skill
compatible with other media (such as voice assistant). Also, Telegram skills are a bit more cumbersome to
write and to test.

"""

from demos.eaglesong.common import *
from kaia.eaglesong.drivers.telegram import TgCommand, TelegramSimplifier

def main():
    update = yield None
    username = update.message.chat.username
    chat_id = update.message.chat.id
    yield TgCommand.mock().send_message(
        chat_id = chat_id,
        text = f'Hello, {username}. Say anything and I will repeat. Or /start to reset.'
    )
    while True:
        update = yield Listen()
        message_text = update.message.text
        yield TgCommand.mock().send_message(chat_id=chat_id, text=message_text)


bot = Bot("telegram", TelegramSimplifier(main), add_telegram_filter=False)

if __name__ == '__main__':
    run(bot)