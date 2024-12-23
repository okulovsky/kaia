from ...framework import IDecider
import string
import random

class FakeText(IDecider):
    def __call__(self, prefix = '', length = 50):
        characters = string.ascii_letters + string.digits + string.punctuation
        random_text = prefix+' '+''.join(random.choices(characters, k=length))
        return random_text
