import time
from unittest import TestCase
from brainbox.framework import IDecider, BrainBoxTask, BrainBoxApi
from pprint import pprint

class TestDecider(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, arg):
        return f'OK-{arg}'

class BigLoadTestCase(TestCase):
    def dont_test_big_load(self):
        with BrainBoxApi.Test([TestDecider()]) as api:
            tasks = [BrainBoxTask(id=str(i), decider='test', arguments=dict(arg=i)) for i in range(100000)]
            api.add(tasks)
            while True:
                summary = api.summary()
                finished = sum(s['finished'] for s in summary)
                print(finished)
                time.sleep(1)
                if finished == len(tasks):
                    break


