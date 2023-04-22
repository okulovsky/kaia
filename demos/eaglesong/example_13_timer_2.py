"""
The cleaner way of timer's implementation is to push timer update to the same routine
as customer's input normally goes.

In this case, however, we need a _dispatcher_ that would understand if the update needs to be sent
in the main skill or elsewhere.

Generally, such dispatchers are needed in chatbot anyway: imagine, that you are in the
middle of the skill, but suddenly want to send timer. In this case, it would be a dispatcher's
role to understand that the timer skill needs to be activated, and the current skill needs to be suspended.
"""

from demos.eaglesong.common import *
from kaia.eaglesong.amenities.dispatcher import Dispatcher

class TimerBot(Dispatcher):
    def __init__(self):
        super(TimerBot, self).__init__()
        self.add_skill('timer', self.on_timer)
        self.add_skill('main', self.main)
        self.timer_state = False
        self.value = 0

    def on_timer(self, context: BotContext):
        if self.timer_state:
            yield self.value
            self.value+=1
        else:
            yield Return()

    def main(self, context: BotContext):
        yield 'This bot will send you an integer every second. Enter /toggle to pause/resume'
        while True:
            yield Listen()
            if context.input == '/toggle':
                self.timer_state=not self.timer_state
                yield f"Timer set to {self.timer_state}"

    def dispatch(self, context: BotContext):
        if isinstance(context.input, TimerTick):
            return 'timer'
        else:
            return 'main'

bot = Bot("timer2", factory=TimerBot, timer=True)

if __name__ == '__main__':
    run(bot)