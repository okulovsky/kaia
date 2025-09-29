from abc import ABC, abstractmethod
from grammatron import *
from eaglesong import Listen
from kaia import KaiaSkillBase, ButtonPressedEvent, ButtonGridCommand


class IMusicPlayer(ABC):
    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def previous(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def resume(self):
        pass


MUSIC = VariableDub("music")

class Intents(TemplatesCollection):
    play = Template(
        "Play music!",
        f"Play {MUSIC} music!"
    )


class MusicSkill(KaiaSkillBase):
    def __init__(self, name_to_player: dict[str, IMusicPlayer]):
        self.name_to_player = name_to_player
        template = Intents.play.substitute(music = OptionsDub(list(self.name_to_player)))
        super().__init__(Intents.get_templates(template), None)

    def get_type(self):
        return KaiaSkillBase.Type.MultiLine

    def should_start(self, input) -> bool:
        return input in Intents.play

    def should_proceed(self, input) -> bool:
        return isinstance(input, ButtonPressedEvent)

    def _get_playlist_buttons(self):
        builder = ButtonGridCommand.Builder()
        for playlist in self.name_to_player:
            builder.add(playlist, dict(playlist=playlist))
        return builder.to_grid()

    def _get_control_buttons(self, playing):
        builder = ButtonGridCommand.Builder(5)
        builder.add('Previous', dict(action='previous'))
        if playing:
            builder.add('Playing', None)
            builder.add('Pause', dict(action='pause'))
        else:
            builder.add('Resume', dict(action='resume'))
            builder.add('Paused', None)
        builder.add('Next', dict(action='next'))
        builder.add('Stop', dict(action='stop'))
        return builder.to_grid()

    def play_music(self, player: IMusicPlayer):
        player.play()
        playing = True
        while True:
            yield self._get_control_buttons(playing)
            action = yield Listen()
            if not isinstance(action, ButtonPressedEvent):
                raise ValueError("Button pressed is expected")
            yield ButtonGridCommand.empty()
            action = action.button_feedback['action']
            if action == 'pause':
                player.pause()
                playing = False
            elif action == 'resume':
                player.resume()
                playing = True
            elif action == 'stop':
                player.stop()
                break
            elif action == 'previous':
                player.previous()
            elif action == 'next':
                player.next()

    def _run_with_menu(self):
        yield self._get_playlist_buttons()
        result = yield Listen()
        yield ButtonGridCommand.empty()
        player = self.name_to_player[result.button_feedback['playlist']]
        yield from self.play_music(player)


    def run(self):
        input: Utterance = yield
        music = input.get_field()
        if music is None:
            yield from self._run_with_menu()
        else:
            player = self.name_to_player[music]
            yield from self.play_music(player)








