from unittest import TestCase
from eaglesong.core import Automaton, Scenario, Return
from avatar.daemon import *
from talents.spotify.skill import SpotifySkill, SpotifyHandler, Playlist
from talents.spotify.skill.skill import Intents
from unittest.mock import MagicMock

def S():
    mock = MagicMock(spec=SpotifyHandler)
    playlists = [
        Playlist("Epic playlist", 'epic'),
        Playlist("Rock playlist", 'rock')
    ]
    return Scenario(automaton_factory=lambda: Automaton(SpotifySkill(mock,playlists).run, None))

class WeatherTestCase(TestCase):
    def test_without_playlist(self):
        (
            S()
            .send(Intents.generic())
            .check(lambda z: isinstance(z, ButtonGridCommand) and len(z.elements)==2)
            .send(ButtonPressedEvent(dict(playlist='epic')))
            .check(ButtonGridCommand, ButtonGridCommand)
            .validate()
        )

    def test_playlist(self):
        (
            S()
            .send(Intents.playlist('Epic playlist'))
            .check(ButtonGridCommand)
            .validate()
        )

