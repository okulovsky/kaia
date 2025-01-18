from ...framework import IDecider
import string
import random
import time

class FakeText(IDecider):
    def __call__(self, prefix = '', length = 50, time_to_sleep: float|None = None):
        if time_to_sleep is not None:
            time.sleep(time_to_sleep)
        characters = string.ascii_letters + string.digits + string.punctuation
        random_text = prefix+' '+''.join(random.choices(characters, k=length))
        return random_text
