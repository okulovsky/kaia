"""
The bots we saw so far were triggered by the user input. Sometimes the bots should be triggered by some other
means, and in this case the timer is used to poll the bot and produce the output if necessary.

This timer input is fed into the chatflow in the same fashion as the normal input.
"""
from eaglesong.demo.common import *


def main():
    timer_state = False
    timer_value = 0
    yield 'This bot will send you an integer every second. Enter /toggle to pause/resume'
    while True:
        input = yield Listen()
        if isinstance(input, TimerTick) and timer_state:
            yield timer_value
            timer_value += 1
        elif input=='/toggle':
            timer_state = not timer_state
            yield 'Timer set to '+str(timer_state)


bot = Bot("timer1", main, timer = True)


if __name__ == '__main__':
    run(bot)