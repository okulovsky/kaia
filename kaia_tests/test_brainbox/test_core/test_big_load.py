import time
from unittest import TestCase
from kaia.brainbox import IDecider, BrainBoxTask, BrainBoxTestApi
from pprint import pprint

class TestDecider(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, arg):
        return f'OK-{arg}'

class BrainBoxWebServerEmptyTestCase(TestCase):
    def dont_test_all_kinds_of_data(self):
        with BrainBoxTestApi(dict(test=TestDecider())) as api:
            tasks = [BrainBoxTask(str(i), decider='test', arguments=dict(arg=i)) for i in range(100000)]
            api.add(tasks)
            while True:
                summary = api.get_summary()
                finished = sum(s['finished'] for s in summary)
                print(finished)
                time.sleep(1)
                if finished == len(tasks):
                    break


