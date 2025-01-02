"""
Such handling of the timer's signals brings the problem for the multi-step skills that expect
a certain input (such as menu). Obviously, they are going to be ruined by TimerTicks coming unexpectedly.

To avoid this, Timer signals have to be filtered out of normal flow. Here is the full code of how to do this.
At some point there will be some abstractions to make this in the easier way,
but at this point, let's see how it works under the hood. If you want to somehow manipulate with
input or outputs of skill A inside the skill B, you must isolate A inside the Automaton.
Automaton is an entity that translates these chatflows with all the `yield` into a normal function that
consumes one input and produces one output.

"""

from eaglesong.demo.common import *
from eaglesong.demo.example_08_menu_2 import create_menu

def main():
    context = yield ContextRequest()
    timer_state = False
    timer_value = 0
    menu_aut = None #type: Optional[Automaton]
    yield 'This bot will send you an integer every second. Enter /toggle to pause/resume, or /menu to open menu.'
    input = yield Listen()
    while True:
        if isinstance(input, TimerTick):
            if timer_state:
                yield timer_value
                timer_value+=1
            input = yield Listen()
            continue
        if input == '/toggle':
            timer_state = not timer_state
            yield 'Timer set to '+str(timer_state)
            input = yield Listen()
            continue

        if input == '/menu':
            menu_aut = Automaton(create_menu(), context)

        if menu_aut is not None:
            result = menu_aut.process(input)
            if isinstance(result, AutomatonExit):
                menu_aut = None
                input = yield Listen()
            else:
                input = yield result
            continue

        yield f'Unexpected input: {input}'
        input = yield Listen()



bot = Bot("timer2", main, timer=True)

if __name__ == '__main__':
    run(bot)