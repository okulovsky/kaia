"""
Chat flows we were writing so far were passive: they would only reply
to the customer's input. However, sometimes we want actions to happen
by themselves. That could be a bot initiative or delayed action: when
customer initiated the content's production that took some time and now
it's ready and needs to be sent.

To do this we can use timers. The simplest (although horrible) way is
to assign a separate `Routine` to timer.

It's horrible because the main Routine and the timer Routine are completely separate.
So the example below will only work for one customer. For more customers, you would
need to store the `timer_state` and `value` in some storage, chared benween `main`
and `on_timer`, and restore the state from there. This is **not** what we want,
so the next example will provide a cleaner way to do the same.
"""
from demos.eaglesong.common import *


timer_state = False
value = 0


def on_timer(context: BotContext):
    global timer_state, value
    if timer_state:
        yield value
        value+=1
    else:
        yield Return()


def main(context: BotContext):
    global timer_state, value
    yield 'This bot will send you an integer every second. Enter /toggle to pause/resume'
    while True:
        yield Listen()
        if context.input == '/toggle':
            timer_state=not timer_state
            yield f"Timer set to {timer_state}"


bot = Bot("timer1", main, timer_function = on_timer)


if __name__ == '__main__':
    run(bot)