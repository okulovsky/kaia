from .. import MicState, State
from ..processing import IMonitor

GREEN = "\x1b[32m"
RESET = "\x1b[0m"
RED = "\x1b[31m"
YELL = "\x1b[33m"

FULL = "█"
EMPTY = "·"

class ConsoleMonitor(IMonitor):
    def __init__(self):
        self.state: State|None = None
        self.level: float|None = None
        self.silence_level: float|None = None
        self.max_level: float|None = None

    def on_state_change(self, new_state: State):
        self.state = new_state
        self.draw()

    def on_level(self, level: float):
        self.level = level
        if self.max_level is None or self.level > self.max_level:
            self.max_level = self.level
        self.draw()

    def on_silence_level(self, silence_level: float):
        self.silence_level = silence_level
        if self.max_level is None or self.silence_level > self.max_level:
            self.max_level = self.silence_level
        self.draw()

    def _draw_gauge(self):
        WIDTH = 50
        if self.max_level is None:
            return []
        delta = self.max_level/WIDTH
        x = delta
        first_cross = True
        positions = []
        for i in range(WIDTH):
            if self.level is not None and self.level>=x:
                symbol = FULL
            else:
                symbol = EMPTY
            if self.silence_level is not None and self.silence_level < x:
                if first_cross:
                    color = YELL
                else:
                    color = RED
                    first_cross = False
            else:
                color = GREEN
            positions.append(f'{color}{symbol}')
            x+=delta
        positions.append(RESET)
        return positions

    def draw(self):
        state = 'NONE'
        if self.state is not None:
            state = self.state.mic_state.name
        result = [state.ljust(10)]
        result.extend(''.join(self._draw_gauge()))
        result.extend('   ')
        if self.max_level is not None:
            mx = f'{int(self.max_level*1000):>3}'
        else:
            mx = '---'
        result.append(mx)
        print(''.join(result)+'           \r', end='')














