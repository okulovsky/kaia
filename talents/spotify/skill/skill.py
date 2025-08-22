from .spotify_handler import SpotifyHandler, Playlist
from grammatron import *
from eaglesong import Listen
from kaia import KaiaSkillBase, ButtonPressedEvent, ButtonGridCommand
from yo_fluq import *

PLAYLIST = VariableDub("playlist")

class Intents(TemplatesCollection):
    generic = Template("Play music!")
    playlist = Template(f"Play {PLAYLIST} playlist!")

class SpotifySkill(KaiaSkillBase):
    def __init__(self, handler: SpotifyHandler, playlists: list[Playlist]):
        self.handler = handler
        self.playlists = playlists
        template = Intents.playlist.substitute(**{PLAYLIST.name:OptionsDub([z.name for z in playlists])})
        super().__init__(Intents.get_templates(template), None)

    def get_type(self):
        return KaiaSkillBase.Type.MultiLine

    def should_start(self, input) -> bool:
        return input in Intents.generic or input in Intents.playlist

    def should_proceed(self, input) -> bool:
        return isinstance(input, ButtonPressedEvent) or isinstance(input, str)

    def _get_playlist_buttons(self):
        builder = ButtonGridCommand.Builder()
        for playlist in self.playlists:
            builder.add(playlist.name, dict(playlist=playlist.uri))
        return builder.to_grid()

    def _get_control_buttons(self, in_list, playing):
        builder = ButtonGridCommand.Builder(5 if in_list else 3)
        if in_list:
            builder.add('Previous', dict(action='previous'))
        if playing:
            builder.add('Playing', None)
            builder.add('Pause', dict(action='pause'))
        else:
            builder.add('Resume', dict(action='resume'))
            builder.add('Paused', None)
        if in_list:
            builder.add('Next', dict(action='next'))

        builder.add('Stop', dict(action='stop'))
        return builder.to_grid()

    def _control_playing(self, in_list: bool):
        playing = True
        while True:
            yield self._get_control_buttons(in_list, playing)
            action = yield Listen()
            if not isinstance(action, ButtonPressedEvent):
                raise ValueError("Button pressed is expected")
            yield ButtonGridCommand.empty()
            action = action.button_feedback['action']
            if action == 'pause':
                self.handler.pause()
                playing = False
            elif action == 'resume':
                self.handler.resume()
                playing = True
            elif action == 'stop':
                self.handler.pause()
                break
            elif action == 'previous':
                self.handler.previous()
            elif action == 'next':
                self.handler.next()

    def _run_with_menu(self):
        yield self._get_playlist_buttons()
        result = yield Listen()
        yield ButtonGridCommand.empty()
        self.handler.play_playlist(result.button_feedback['playlist'])
        yield from self._control_playing(True)

    def run(self):
        input: Utterance = yield
        if input in Intents.generic:
            yield from self._run_with_menu()
        elif input in Intents.playlist:
            name = input.get_field()
            playlist = [z for z in self.playlists if z.name == name]
            if len(playlist) == 0:
                raise ValueError(f'Playlist {name} was not found')
            self.handler.play_playlist(playlist[0].uri)
            yield from self._control_playing(True)








