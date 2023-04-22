"""
How do we call other functions from `main`?

The important case is when this function wants to say or do anything on behalf of the bot.
We call such functions "Routines", and to call them, you need to use `yield Subroutine`.
In the following example, we call `questionnaire` subroutine and then get the returned values from it.
It's not a perfect solution, but we will improve it in the following demos.

If it's just a normal Python function, such as `datetime.now()` below, you can of course
just call it and use the returned value normally.
"""

from demos.eaglesong.common import *
from datetime import datetime


def questionnaire(c: BotContext):
    yield 'What is your name?'
    yield Listen()
    name = c.input

    yield f'Where are you from, {name}?'
    yield Listen()
    country = c.input

    yield Return(name, country)


def main(c: BotContext):
    subroutine = Subroutine(questionnaire)
    yield subroutine
    name, country = subroutine.returned_value()

    current_time = datetime.now()
    yield f"Nice to meet you, {name} from {country}! By the way, the current time is {current_time}"


bot = Bot("quest1", main)

if __name__ == '__main__':
    run(bot)