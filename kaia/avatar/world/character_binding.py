from kaia.dub import FieldBinding, Address


class PronounBinding:
    def __init__(self, field_name):
        self.subjective = FieldBinding(Address(field_name, 'pronoun','subjective'))
        self.objective = FieldBinding(Address(field_name, 'pronoun', 'objective'))
        self.possessive = FieldBinding(Address(field_name, 'pronoun', 'possessive'))
        self.reflexive = FieldBinding(Address(field_name, 'pronoun', 'reflexive'))


class CharacterBinding(FieldBinding):
    def __init__(self, field_name: str):
        self._field_name = field_name
        super().__init__(Address(field_name), None)

    @property
    def field_name(self):
        return self._field_name

    @property
    def pronoun(self):
        return PronounBinding(self._address.address[0])

