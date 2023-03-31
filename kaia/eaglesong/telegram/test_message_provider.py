import json

from .telegram_bridge import TgUpdate
from .tg_command import TgCommand
import telegram as tg
from datetime import datetime

class TelegramTestProvider:
    def __init__(self, chat_id, username):
        self.chat_id = chat_id
        self.username = username
        self.running_id = 1

    def _tg_text_message(self, text):
        self.running_id += 1
        return tg.Update(
            update_id=self.running_id,
            message=tg.Message(
                message_id=self.running_id,
                date=datetime.now(),
                chat=tg.Chat(
                    id=self.chat_id,
                    type='private'
                ),
                from_user=tg.User(
                    id=1,
                    first_name=self.username,
                    is_bot=False),
                text=text))

    def text(self, text):
        return TgUpdate(None, self.chat_id, TgUpdate.Type.Text, self._tg_text_message(text), None)

    def start(self):
        return TgUpdate(None, self.chat_id, TgUpdate.Type.Start, self._tg_text_message('/start'), None)

    @staticmethod
    def visualize(log):
        result = []
        for l in log:
            result.append('> ' + l['prompt'].update.to_json())
            for l in l['response']:
                if isinstance(l, TgCommand):
                    v = l.bot_method + "(" + ', '.join(
                        [str(s) for s in l.args] + [f'{k} = {v}' for k, v in l.kwargs.items()]) + ")"
                else:
                    v = str(l)
                result.append('  < ' + v)
        return '\n'.join(result)






