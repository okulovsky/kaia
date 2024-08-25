import re
from abc import ABC, abstractmethod
from ..structures import Dub, DubBinding, ToStrDub
import pickle
from io import BytesIO
import base64

class PredefinedFieldsCache:
    _cache = {}

    @staticmethod
    def get(field: 'IPredefinedField') -> str:
        code = field.get_code()
        if code in PredefinedFieldsCache._cache:
            return PredefinedFieldsCache._cache[code]
        io = BytesIO()
        pickle.dump(field, io)
        b64 = base64.b64encode(io.getvalue()).decode('utf-8')
        result = f'<<<{b64}>>>'
        PredefinedFieldsCache._cache[code] = result
        return result




class IPredefinedField(ABC):
    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_dub(self) -> Dub | DubBinding:
        pass

    def get_code(self):
        parts = [type(self).__name__]
        for k in sorted(self.__dict__):
            parts.append(k)
            parts.append(str(self.__dict__[k]))
        return '/'.join(parts)


    def __str__(self):
        return PredefinedFieldsCache.get(self)


    @staticmethod
    def fix_template_arguments(strings, dubs):
        new_strings = []
        new_dubs = {k :v for k ,v in dubs.items()}
        pattern = '(<<<[^>]+>>>)'
        previous_text_part = ''
        for s in strings:
            new_s = ''
            for part_index, part in enumerate(re.split(pattern, s)):
                if part.startswith('<<<'):
                    data = part[3:-3]
                    try:
                        predefined_field = pickle.loads(base64.b64decode(data.encode('utf-8')))
                    except Exception as ex:
                        raise ValueError(f'Cant unpickle from part {part_index}. Previous text part\n{previous_text_part}') from ex
                    if not isinstance(predefined_field, IPredefinedField):
                        raise ValueError(f'Unpickled object from part {part_index} is not IPredefinedField. Previous text part\n{previous_text_part}')
                    name = predefined_field.get_name()
                    new_s += '{' + name +'}'
                    if name not in new_dubs:
                        new_dubs[name] = predefined_field.get_dub()
                else:
                    previous_text_part = part
                    new_s += part
            new_strings.append(new_s)

        return new_strings, new_dubs


class PredefinedField(IPredefinedField):
    def __init__(self, name: str):
        self._name = name

    def get_name(self) -> str:
        return self._name

    def get_dub(self) -> Dub | DubBinding:
        return ToStrDub()

    @property
    def field_name(self):
        return self._name
