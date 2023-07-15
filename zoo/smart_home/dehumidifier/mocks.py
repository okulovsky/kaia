from .space import Space

class MockHumidity:
    def __init__(self, increment, decrement):
        self.increment = increment
        self.decrement = decrement

    def __call__(self, space: Space):
        if space.humidity.last_value is None:
            space.humidity.current_value = 60
            return

        if space.state.last_value:
            delta = self.decrement
        else:
            delta = self.increment

        space.humidity.current_value = space.humidity.last_value + delta


class MockDehumidifier:
    def __call__(self, space: Space):
        if space.state_request.last_value is not None:
            space.state.current_value = space.state_request.last_value
        else:
            if space.state.last_value is None:
                space.state.current_value = False
            else:
                space.state.current_value = space.state.last_value
