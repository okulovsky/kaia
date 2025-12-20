from ...framework import IDecider
from copy import copy

class Empty(IDecider):
    def __call__(self, **kwargs):
        return copy(kwargs)
