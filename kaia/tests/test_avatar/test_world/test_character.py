from kaia.avatar import Character, CharacterBinding, PronounBinding
from kaia.dub import Template
from unittest import TestCase

FIELD = CharacterBinding('character')
VALUE = dict(character=Character('X', Character.Gender.Feminine))

class CharacterTestCase(TestCase):
    def test_character_binding(self):
        template = Template(
            'Name is {x}',
            x = CharacterBinding('character').get_dub()
        )
        self.assertEqual(
            'Name is X',
            template.to_str(VALUE)
        )

    def test_pronoun_binding(self):
        template = Template(
            'Pronouns are {x}/{y}',
            x=PronounBinding('character').subjective.get_dub(),
            y=PronounBinding('character').objective.get_dub()
        )
        self.assertEqual(
            'Pronouns are she/her',
            template.to_str(VALUE)
        )

    def test_inline_name(self):
        s = f'Name is {FIELD}, pronouns are {FIELD.pronoun.subjective}/{FIELD.pronoun.objective}'
        template = Template(s)

        self.assertEqual(
            'Name is X, pronouns are she/her',
            template.to_str(VALUE)
        )

