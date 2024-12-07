import re
from abc import ABC, abstractmethod
from ..structures import Dub, IDubBinding
import pickle
from io import BytesIO
import base64

class InlineBindingCache:
    _cache = {}

    @staticmethod
    def get(field: 'IInlineBinding') -> str:
        code = field.get_hash()
        if code in InlineBindingCache._cache:
            return InlineBindingCache._cache[code]
        io = BytesIO()
        pickle.dump(field, io)
        b64 = base64.b64encode(io.getvalue()).decode('utf-8')
        result = f'<<<{b64}>>>'
        InlineBindingCache._cache[code] = result
        return result




class IInlineBinding(ABC):
    @abstractmethod
    def get_hash(self) -> str:
        pass

    @abstractmethod
    def get_dub(self) -> Dub | IDubBinding:
        pass


    def __str__(self):
        return InlineBindingCache.get(self)

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
                    if not isinstance(predefined_field, IInlineBinding):
                        raise ValueError(f'Unpickled object from part {part_index} is not IPredefinedField. Previous text part\n{previous_text_part}')
                    name = predefined_field.get_hash()
                    new_s += '{' + name +'}'
                    if name not in new_dubs:
                        new_dubs[name] = predefined_field.get_dub()
                else:
                    previous_text_part = part
                    new_s += part
            new_strings.append(new_s)

        return new_strings, new_dubs


