from typing import *
from .primitives import *

class RoutineBase:
    def instantiate(self, context: Context):
        raise NotImplementedError()

    def get_name(self):
        raise NotImplementedError()

    def returned_value(self):
        return getattr(self,'_returned_value', None)

    @staticmethod
    def subroutine(method, *args, **kwargs):
        return Subroutine(method, *args, **kwargs)


    @staticmethod
    def ensure(obj) -> 'RoutineBase':
        if isinstance(obj, RoutineBase):
            return obj
        return Subroutine(obj)

    @staticmethod
    def interpretable(obj, *translators: Callable):
        obj = RoutineBase.ensure(obj)
        for translator in translators:
            obj = translator(obj)
        return obj



class Routine(RoutineBase):
    def run(self, context):
        raise NotImplementedError()

    def instantiate(self, context: Context):
        return self.run(context)

    def get_name(self):
        return type(self).__name__




class Subroutine(RoutineBase):
    def __init__(self, method, *args, **kwargs):
        self.method=method
        self.name = method.__name__
        self.kwargs = kwargs
        self.args = args

    def instantiate(self, context: Context):
        return self.method(context,*self.args, **self.kwargs)

    def get_name(self):
        full_name=self.name
        if len(self.args)>0:
            full_name+='_'+'_'.join([str(z) for z in self.args])
        if len(self.kwargs)>0:
            full_name+='_'+'_'.join([key+'_'+self.kwargs[key] for key in self.kwargs])
        return full_name


class ConstantRoutine(Routine):
    def __init__(self, *values):
        self.values = values

    def run(self, context):
        for value in self.values:
            yield value


class PushdownFilter(Routine):
    def __init__(self, root: RoutineBase):
        self.root = root

    def _run_recursive(self, c, subroutine: RoutineBase):
        ret_command = None
        for output in subroutine.instantiate(c):
            if isinstance(output, Return):
                ret_command = output
                break
            elif isinstance(output, RoutineBase):
                for suboutput in self._run_recursive(c, output):
                    if not isinstance(suboutput, Return):
                        yield suboutput
            else:
                yield output
        ret_value = ret_command.return_value if ret_command is not None else None
        subroutine._returned_value = ret_value
        c.set_input(ret_value)

    def run(self, context):
        return self._run_recursive(context, self.root)






