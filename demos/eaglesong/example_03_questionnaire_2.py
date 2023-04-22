"""
To simplify `Subroutine` calling, you may use `context.input` field.

Generally, after each `yield` the field `context.input` contains some details
about the result of this command. The same is true for `yield Listen()`:
it returns the result of listening.

It is important to retrieve the `context.input` immediately after `yield` and store it
for future use, as it might change after other `yields`.
"""
from demos.eaglesong.common import *

def questionnaire(context: BotContext):
    yield 'What is your name?'
    yield Listen()
    name = context.input

    yield f'Where are you from, {name}?'
    yield Listen()
    country = context.input

    yield Return(name, country)

def main(context: BotContext):
    yield Subroutine(questionnaire)
    name, country = context.input
    yield f"Nice to meet you, {name} from {country}!"
    message_id = context.input
    yield f"By the way, message id was {message_id}"


bot = Bot("quest2", main)


if __name__ == '__main__':
    run(bot)