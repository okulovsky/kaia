from kaia.narrator import Character, CharacterDubBinding, PronounDubBinding, CharacterWorldField
from kaia.dub import Template
from unittest import TestCase

FIELD = CharacterWorldField('character')
VALUE = dict(character=Character('X', Character.Gender.Feminine))

class CharacterTestCase(TestCase):
    def test_character_binding(self):
        template = Template(
            'Name is {x}',
            x = CharacterDubBinding('character')
        )
        self.assertEqual(
            'Name is X',
            template.to_str(VALUE)
        )

    def test_pronoun_binding(self):
        template = Template(
            'Pronouns are {x}/{y}',
            x=PronounDubBinding(0, ('character',)),
            y=PronounDubBinding(1, ('character',))
        )
        self.assertEqual(
            'Pronouns are she/her',
            template.to_str(VALUE)
        )

    def test_inline_name(self):
        template = Template(f'Name is {FIELD}, pronouns are {FIELD.pronoun.subjective}/{FIELD.pronoun.objective}')
        print(template.attached_dubs)

        self.assertEqual(
            'Name is X, pronouns are she/her',
            template.to_str(VALUE)
        )

