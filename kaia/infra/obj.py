from collections import OrderedDict


_INITIALIZED_KEY = '_Obj__initialized'
_EXCEPTIONS = {_INITIALIZED_KEY }

class Obj(OrderedDict):
    def __init__(self, **kwargs):
        super(Obj, self).__init__(**kwargs)
        self.__initialized = True

    def __setattr__(self, key, value):
        if _INITIALIZED_KEY not in self.__dict__:
            self.__dict__[key] = value
        else:
            if key in _EXCEPTIONS:
                raise ValueError('{0} attribute cannot be set, it is a reserved field'.format(key))
            self[key] = value

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self[key]=value
        return self

    def remove(self, *args):
        for key in args:
            del self[key]
        return self

    def __repr__(self):
        return dict.__repr__(self)

    def __getattr__(self, item):
        if _INITIALIZED_KEY not in self.__dict__: #pragma: no cover
            return self.__dict__[item]
        else:
            if item in _EXCEPTIONS: #pragma: no cover
                return self.__dict__[item]
            else:
                try:
                    return self[item]
                except:
                    raise AttributeError(item)


    @staticmethod
    def _make_pretty(obj):
        if isinstance(obj,dict):
            return Obj( **{key:Obj._make_pretty(obj[key]) for key in obj})
        elif isinstance(obj,list):
            return [Obj._make_pretty(o) for o in obj]
        else:
            return obj

    @staticmethod
    def create(d):
        return Obj._make_pretty(d)