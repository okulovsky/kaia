from kaia.skills.music_skill import IMusicPlayer
from .spotify_handler import SpotifyHandler, Playlist

class SpotifyPlaylistPlayer(IMusicPlayer):
    def __init__(self, handler: SpotifyHandler, playlist: Playlist):
        self.handler = handler
        self.playlist = playlist

    def play(self):
        self.handler.play_playlist(self.playlist.uri)

    def next(self):
        self.handler.next()

    def previous(self):
        self.handler.previous()

    def pause(self):
        self.handler.pause()

    def stop(self):
        self.handler.pause()

    def resume(self):
        self.handler.resume()

