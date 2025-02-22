from ...framework import IDecider

class EmptyTask(IDecider):
    def __call__(self):
        return "OK"
