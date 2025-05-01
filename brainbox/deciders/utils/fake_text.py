from ...framework import IDecider
import string
import random
import time

class FakeText(IDecider):
    def __call__(self, prefix = '', length = 0, time_to_sleep: float|None = None):
        if time_to_sleep is not None:
            time.sleep(time_to_sleep)
        characters = string.ascii_letters + string.digits + string.punctuation
        if length>0:
            result = prefix+' '+''.join(random.choices(characters, k=length))
        else:
            result = prefix
        return result
