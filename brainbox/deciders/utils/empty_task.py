from ...framework import IDecider

class EmptyDecider(IDecider):
    def __call__(self):
        return "OK"
