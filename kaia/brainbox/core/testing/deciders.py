import time
from ..decider import IDecider

class WaitingDecider(IDecider):
    def __init__(self,
                 processing_time = 1,
                 warmup_time = 2,
                 cooldown_time = 0.5
                 ):
        self.processing_time = processing_time
        self.warmup_time = warmup_time
        self.cooldown_time = cooldown_time

    def warmup(self):
        time.sleep(self.warmup_time)

    def cooldown(self):
        time.sleep(self.cooldown_time)

    def run(self, arg = None):
        time.sleep(self.cooldown_time)
        if arg is None:
            return 'OK'
        return f"OK-{arg}"


class CollectingDecider(IDecider):
    def warmup(self):
        pass

    def cooldown(self):
        pass

    def run(self, **args):
        return dict(collected=True, arg=args)

