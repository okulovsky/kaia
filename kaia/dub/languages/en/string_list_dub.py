from ...core import ToStrDub

class StringListDub(ToStrDub):
    def to_str(self, value):
        value = list(value)
        if len(value) == 0:
            raise ValueError('Not defined for empty collections')
        elif len(value) == 1:
            return value[0]
        elif len(value) == 2:
            return value[0]+' and '+value[1]
        else:
            return ', '.join(value[:-1])+' and '+value[-1]
