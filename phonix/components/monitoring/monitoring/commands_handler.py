import datetime
from avatar.messaging import IMessage
from ....daemon import SoundPlayStarted
from avatar.services import SoundConfirmation



class CommandsHandler:
    def __init__(self):
        # pending PlayStarted: id → message
        self._commands: dict[str, SoundPlayStarted] = {}
        # slot index for each command id (to avoid vertical overlap)
        self._command_to_level: dict[str, int] = {}
        # confirmed bars
        self._shapes: list[dict] = []
        self._annotations: list[dict] = []

    def add(self, now: datetime.datetime, item: IMessage):
        if isinstance(item, SoundPlayStarted):
            # assign next slot for stacking
            level = len(self._commands)
            self._commands[item.envelop.id] = item
            self._command_to_level[item.envelop.id] = level

        elif isinstance(item, SoundConfirmation):
            # for each referenced PlayStarted, close its bar
            for cmd_id in item.envelop.confirmation_for:
                if cmd_id in self._commands:
                    end   = (item.envelop.timestamp - now).total_seconds()
                    self._make_bar_and_annotation(now, cmd_id, end, 'lightgreen')
                    del self._commands[cmd_id]
                    del self._command_to_level[cmd_id]



    def _make_bar_and_annotation(self, now: datetime.datetime, id: str, x1: float, color: str):
        y0 = 0 #ignoring the level atm
        y1 = 1
        x0 = (self._commands[id].envelop.timestamp - now).total_seconds()

        shape = {
            'type': 'rect',
            'xref': 'x', 'yref': 'paper',
            'x0': x0, 'x1': x1,
            'y0': y0, 'y1': y1,
            'fillcolor': color,
            'opacity': 0.5,
            'line': {'width': 0},
            'layer': 'below',
        }
        annot = {
            'xref': 'x', 'yref': 'paper',
            'x': (x0 + x1) / 2, 'y': (y0 + y1) / 2,
            'text': str(self._commands[id].metadata),
            'showarrow': False,
            'font': {'size': 10},
            'align': 'center',
        }
        self._shapes.append(shape)
        self._annotations.append(annot)

    def get_shapes_and_annotations(self, now: datetime):
        """
        Returns:
          - all confirmed bars (_shapes/_annotations)
          - plus bars for any pending commands (x1 == 0)
        """
        for cmd_id in self._commands:
            self._make_bar_and_annotation(now, cmd_id, 0, 'yellow')

        return self._shapes, self._annotations