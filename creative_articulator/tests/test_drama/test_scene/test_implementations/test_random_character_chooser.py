import unittest
from unittest.mock import patch

from creative_articulator.drama.data import Node, Character, CharacterReference, Message
from creative_articulator.drama.scene import Actors, ISceneRules
from creative_articulator.drama.driver import SceneState
from creative_articulator.drama.scene.implementations.random_character_chooser import RandomCharacterChooser

_RANDOM_CHOICE = 'creative_articulator.drama.scene.implementations.random_character_chooser.random.choice'


def _character(name: str) -> Character:
    return Character(name, Character.Gender.Neutral, f'{name} description')


class _Rules(ISceneRules):
    def __init__(self, actors: Actors):
        self.actors = actors

    def get_actors(self) -> Actors:
        return self.actors


def _scene(protagonist_name: str, npc_names: list[str], history: list[tuple[str, bool]]) -> Node:
    """`history` is a list of (speaker, from_user) tuples, oldest message first."""
    protagonist = CharacterReference(_character(protagonist_name))
    npcs = CharacterReference(*[_character(name) for name in npc_names])
    scene = Node()
    scene[ISceneRules] = _Rules(Actors(protagonist, npcs))
    state = scene[SceneState]
    for speaker, from_user in history:
        state.messages.append(Message.from_text('text', speaker, from_user))
    return scene


class TestRandomCharacterChooser(unittest.TestCase):
    def setUp(self):
        self.chooser = RandomCharacterChooser()

    def test_returns_none_when_a_response_was_already_given_this_turn(self):
        scene = _scene('Alex', ['Bob', 'Carol'], [])
        result = self.chooser.choose_next_speaker(scene, 1)
        self.assertIsNone(result)

    def test_ignores_message_history_once_a_response_was_already_given(self):
        # Even a scene with no candidates left would still be irrelevant here:
        # responses_count > 0 short-circuits before the history is even read.
        scene = _scene('Alex', [], [])
        result = self.chooser.choose_next_speaker(scene, 1)
        self.assertIsNone(result)

    def test_returns_exactly_one_character_not_a_collection(self):
        scene = _scene('Alex', ['Bob', 'Carol'], [])
        result = self.chooser.choose_next_speaker(scene, 0)
        self.assertIsInstance(result, Character)

    def test_no_messages_yet_everyone_is_tied_at_zero(self):
        scene = _scene('Alex', ['Bob', 'Carol'], [])
        with patch(_RANDOM_CHOICE) as choice:
            choice.side_effect = lambda seq: seq[0]
            self.chooser.choose_next_speaker(scene, 0)
        candidates = choice.call_args[0][0]
        self.assertEqual({'Bob', 'Carol'}, {c.name for c in candidates})

    def test_only_characters_with_the_minimal_count_are_candidates(self):
        scene = _scene('Alex', ['Bob', 'Carol', 'Dave'], [
            ('Alex', True),
            ('Bob', False),
        ])
        with patch(_RANDOM_CHOICE) as choice:
            choice.side_effect = lambda seq: seq[0]
            self.chooser.choose_next_speaker(scene, 0)
        candidates = choice.call_args[0][0]
        # Bob already spoke once (count 1) since the last user message; Carol and
        # Dave are still at the minimal count (0), so only they are candidates.
        self.assertEqual({'Carol', 'Dave'}, {c.name for c in candidates})

    def test_everyone_tied_at_a_nonzero_count_are_still_all_candidates(self):
        # Nothing forces the minimal count to be zero: if every character has
        # already spoken the same number of times since the last user message,
        # they're all still tied for the minimum and remain candidates. It's
        # the caller's job (via responses_count) to stop asking after one pick.
        scene = _scene('Alex', ['Bob', 'Carol'], [
            ('Alex', True),
            ('Bob', False),
            ('Carol', False),
        ])
        with patch(_RANDOM_CHOICE) as choice:
            choice.side_effect = lambda seq: seq[0]
            result = self.chooser.choose_next_speaker(scene, 0)
        candidates = choice.call_args[0][0]
        self.assertEqual({'Bob', 'Carol'}, {c.name for c in candidates})
        self.assertIsNotNone(result)

    def test_history_before_the_last_user_message_is_ignored(self):
        scene = _scene('Alex', ['Bob', 'Carol'], [
            ('Bob', False), ('Bob', False), ('Bob', False),  # Bob spoke a lot, long ago
            ('Alex', True),  # then the user spoke
            # nobody has spoken since
        ])
        with patch(_RANDOM_CHOICE) as choice:
            choice.side_effect = lambda seq: seq[0]
            self.chooser.choose_next_speaker(scene, 0)
        candidates = choice.call_args[0][0]
        # Bob's earlier messages predate the last user message, so they don't
        # count against him: he's eligible again, tied with Carol at 0.
        self.assertEqual({'Bob', 'Carol'}, {c.name for c in candidates})

    def test_scans_all_the_way_to_the_top_when_no_user_message_exists(self):
        scene = _scene('Alex', ['Bob', 'Carol'], [
            ('Bob', False),
        ])
        with patch(_RANDOM_CHOICE) as choice:
            choice.side_effect = lambda seq: seq[0]
            self.chooser.choose_next_speaker(scene, 0)
        candidates = choice.call_args[0][0]
        self.assertEqual({'Carol'}, {c.name for c in candidates})

    def test_tie_is_broken_randomly(self):
        scene = _scene('Alex', ['Bob', 'Carol'], [])
        with patch(_RANDOM_CHOICE) as choice:
            choice.return_value = _character('Carol')
            result = self.chooser.choose_next_speaker(scene, 0)
        self.assertEqual('Carol', result.name)
        candidates = choice.call_args[0][0]
        self.assertEqual({'Bob', 'Carol'}, {c.name for c in candidates})


if __name__ == '__main__':
    unittest.main()
