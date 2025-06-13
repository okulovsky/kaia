"""
## Questionnaire: Calling other functions

How do we call other functions from `main`?

If it's just a normal Python function, such as `datetime.now()` below, you can of course
just call it and use the returned value normally.

But if this function represents chat flow, you need to use `yield from`.

Please note the difference between `yield Listen()` and `return name, country` in `questionnaire`.
`yield Listen()` kinda-return `Listen()` object, but this is not a true return, it doesn't terminate the function
execution. `return name, country` is a true return: it terminates the function and the value `(name, country)`
is assigned to the result of the whole `yield from questionnaire()` call
(and thus to `name, country` variables in `main` method).

"""

from eaglesong.demo.common import *
from datetime import datetime


def questionnaire():
    yield 'What is your name?'
    name = yield Listen()

    yield f'Where are you from, {name}?'
    country = yield Listen()

    return name, country


def main():
    name, country = yield from questionnaire()
    current_time = datetime.now()
    yield f"Nice to meet you, {name} from {country}! By the way, the current time is {current_time}"


bot = Bot("quest", main)

if __name__ == '__main__':
    run(bot)