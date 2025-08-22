from datetime import datetime, timedelta
from ..daemon import TimerEvent

class TestTimeFactory:
    def __init__(self, current:datetime = None):
        if current is None:
            current = datetime(2020,1,1)
        self._current = current

    def delta(self, value: float) -> 'TestTimeFactory':
        ttf = TestTimeFactory(self._current)
        return ttf.shift(value)

    def shift(self, value: float) -> 'TestTimeFactory':
        self._current += timedelta(seconds=value)
        return self

    def event(self):
        return TimerEvent(self._current)

    def current(self):
        return self._current

    def __call__(self):
        return self._current





