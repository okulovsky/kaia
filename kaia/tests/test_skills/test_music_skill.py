from unittest import TestCase
from eaglesong.core import Automaton, Scenario, Return
from avatar.daemon import ButtonPressedEvent, ButtonGridCommand
from avatar.daemon.music_service import Playlist, MusicStartCommand
from kaia.skills.music_skill import MusicSkill, Intents


PLAYLISTS = [
    Playlist("Epic playlist", 'epic'),
    Playlist("Rock playlist", 'rock'),
]

def S():
    return Scenario(automaton_factory=lambda: Automaton(MusicSkill(PLAYLISTS).run, None))


class MusicSkillTestCase(TestCase):
    def test_without_playlist(self):
        (
            S()
            .send(Intents.play.utter())
            .check(lambda z: isinstance(z, ButtonGridCommand) and len(z.elements) == 2)
            .send(ButtonPressedEvent(dict(playlist='Epic playlist')))
            .check(ButtonGridCommand, lambda z: isinstance(z, MusicStartCommand) and z.id.name == 'Epic playlist', Return)
            .validate()
        )

    def test_with_playlist(self):
        (
            S()
            .send(Intents.play.utter(music='Epic playlist'))
            .check(lambda z: isinstance(z, MusicStartCommand) and z.id.name == 'Epic playlist', Return)
            .validate()
        )
