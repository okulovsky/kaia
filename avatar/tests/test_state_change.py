from avatar import AvatarApi, AvatarSettings
from unittest import TestCase

class StateChangeTestCase(TestCase):
    def test_state_change(self):
        settings = AvatarSettings()
        with AvatarApi.Test(settings) as api:
            api.state_change({'a': 'A', 'b': 'B'})
            self.assertEqual(
                {'character': 'character_0', 'a': 'A', 'b': 'B'},
                api.state_get()
            )
            with api.push_state(dict(a='X', c='C')):
                self.assertEqual(
                    {'a': 'X', 'b': 'B', 'c': 'C', 'character': 'character_0'},
                    api.state_get()
                )
            self.assertEqual(
                {'character': 'character_0', 'a': 'A', 'b': 'B', 'c': None},
                api.state_get()
            )

