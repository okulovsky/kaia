from .union_dub import UnionDub
from .set_dub import SetDub
class SetUnionDub(UnionDub):
    def __init__(self, *dubs: SetDub):
        strings = []
        dubs_dict = {}
        names = []
        for i, dub in enumerate(dubs):
            name = f'dub_{i}'
            strings.append('{'+name+'}')
            dubs_dict[name] = dub
            dub_name = dub.get_name()
            names.append(dub_name)
        self._name = '[Union]: '+','.join(names)
        self._dubs = dubs
        sequences = UnionDub.create_sequences(strings, dubs_dict, self._name)
        super().__init__(
            sequences,
            self._value_to_dict,
            self._dict_to_value,
            False
        )

    def _dict_to_value(self, d):
        key = list(d)
        if len(key)!=1:
            raise ValueError('Impossible state: should be exactly one value in a dict')
        return d[key[0]]

    def _value_to_dict(self, v):
        dct = {}
        for index, dub in enumerate(self._dubs):
            if v in dub.get_all_values():
                dct[f'dub_{index}'] = v
        if len(dct)==0:
            raise ValueError("Value was not found in any of the dubs")
        return dct





