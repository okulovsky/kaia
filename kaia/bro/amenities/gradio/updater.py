from datetime import datetime

class Updater:
    def __init__(self, update_every_in_seconds, function):
        self.update_every_in_seconds = update_every_in_seconds
        self.function = function
        self.last_call = None
        self.data = None

    def __call__(self):
        now = datetime.now()
        if self.last_call is None or (now - self.last_call).total_seconds() > self.update_every_in_seconds:
            self.data = self.function()
            self.last_call = now
        return self.data