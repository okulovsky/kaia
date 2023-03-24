class SubroutineBase:
    def instantiate(self, first_argument):
        raise NotImplementedError()

    def get_name(self):
        raise NotImplementedError()

    @staticmethod
    def ensure(f):
        if isinstance(f, SubroutineBase):
            return f
        if callable(f):
            return FunctionalSubroutine(f)
        raise ValueError(f'Expected SubroutineBase or callable, but was {f}')


class Subroutine(SubroutineBase):
    def run(self, c):
        raise NotImplementedError()

    def instantiate(self, first_argument):
        return self.run(first_argument)

    def get_name(self):
        return type(self).__name__


class FunctionalSubroutine(SubroutineBase):
    def __init__(self, method, *args, **kwargs):
        self.method=method
        self.name = method.__name__
        self.kwargs = kwargs
        self.args = args

    def instantiate(self, first_argument):
        return self.method(first_argument,*self.args, **self.kwargs)

    def get_name(self):
        full_name=self.name
        if len(self.args)>0:
            full_name+='_'+'_'.join([str(z) for z in self.args])
        if len(self.kwargs)>0:
            full_name+='_'+'_'.join([key+'_'+self.kwargs[key] for key in self.kwargs])
        return full_name



