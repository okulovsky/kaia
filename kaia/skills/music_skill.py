from grammatron import *
from eaglesong import Listen
from kaia import KaiaSkillBase, ButtonPressedEvent, ButtonGridCommand
from avatar.daemon.music_service import Playlist, MusicStartCommand


MUSIC = VariableDub("music")

class Intents(TemplatesCollection):
    play = Template(
        "Play music!",
        f"Play {MUSIC} music!"
    )

class MusicSkill(KaiaSkillBase):
    def __init__(self, playlists: list[Playlist]):
        self.playlists = playlists
        template = Intents.play.substitute(music = OptionsDub([p.name for p in playlists]))
        super().__init__(Intents.get_templates(template), None)

    def get_type(self):
        return KaiaSkillBase.Type.MultiLine

    def should_start(self, input) -> bool:
        return input in Intents.play

    def should_proceed(self, input) -> bool:
        return isinstance(input, ButtonPressedEvent)

    def _get_playlist_buttons(self):
        builder = ButtonGridCommand.Builder()
        for playlist in self.playlists:
            builder.add(playlist.name, dict(playlist=playlist.name))
        return builder.to_grid()

    def _run_with_menu(self):
        yield self._get_playlist_buttons()
        result = yield Listen()
        yield ButtonGridCommand.empty()
        return result.button_feedback['playlist']


    def run(self):
        input: Utterance = yield
        music = input.value.get('music')
        if music is None:
            music = yield from self._run_with_menu()

        selected = next(z for z in self.playlists if z.name == music)
        yield MusicStartCommand(selected)








