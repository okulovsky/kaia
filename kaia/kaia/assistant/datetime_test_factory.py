from datetime import datetime, timedelta

class DateTimeTestFactory:
    def __init__(self):
        self.dt = datetime(2023,2,10)

    def add(self, seconds: int):
        self.dt += timedelta(seconds = seconds)

    def __call__(self):
        return self.dt