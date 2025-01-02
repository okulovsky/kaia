import uuid

from eaglesong.core import Translator, TranslatorInputPackage, TranslatorOutputPackage
from eaglesong.drivers.telegram import primitives as prim
from .primitives import TgContext, TgCommand, TgUpdatePackage, TgChannel, TgFunction
import telegram as tg
import tempfile
from pathlib import Path
import os
import traceback


BUTTON_PREFIX = 'button_'

def _translate_context(context: TgContext):
    return prim.BotContext(context.chat_id)


class TempFile:
    def __init__(self, path: Path, dont_delete: bool = False):
        self.path = path
        self.dont_delete = dont_delete

    def __enter__(self):
        os.makedirs(self.path.parent, exist_ok=True)
        if self.path.is_file():
            os.unlink(self.path)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.dont_delete:
            if self.path.is_file():
                try:
                    os.unlink(self.path)
                except:
                    print("Cannot delete test file:\n"+traceback.format_exc())


def _translate_input(input_pack: TranslatorInputPackage):
    inner_message = input_pack.outer_input
    if not isinstance(inner_message, TgUpdatePackage):
        return inner_message
    channel = inner_message.channel
    update = inner_message.update #type: tg.Update
    if channel == TgChannel.Callback:
        button_id = update.callback_query.data
        if not button_id.startswith(BUTTON_PREFIX):
            raise ValueError(f'Bad update: {inner_message.update}')
        return prim.SelectedOption(button_id[len(BUTTON_PREFIX):])
    elif channel == TgChannel.Start or channel == TgChannel.Text:
        return update.message.text
    elif channel == TgChannel.Timer:
        return prim.TimerTick()
    elif channel == TgChannel.Voice:
        file_id = update.message.voice.file_id
        file_update = yield TgCommand.mock().get_file(file_id = file_id)
        file = file_update.update #type: tg.File
        bytearray_update = yield TgFunction(file.download_as_bytearray)
        bytearray = bytearray_update.update
        return prim.Audio(bytearray, None)
    elif channel == TgChannel.Feedback:
        if isinstance(inner_message.update, tg.Message):
            return inner_message.update.message_id
        else:
            return inner_message.update
    raise ValueError(f'cannot translate content in channel {inner_message.channel}')


def _get_content_arg(message):
    if isinstance(message, str) or isinstance(message, int) or isinstance(message, float):
        return dict(text=str(message))
    return None


def _get_keyboard(options):
    column_count = 3
    buttons = []
    buffer = []
    for option in options:
        item = tg.InlineKeyboardButton(option, callback_data=BUTTON_PREFIX+option)
        buffer.append(item)
        if column_count is not None and len(buffer) > column_count:
            buttons.append(buffer)
            buffer = []
    if len(buffer) > 0:
        buttons.append(buffer)
    keyboard = tg.InlineKeyboardMarkup(buttons)
    return keyboard


def _translate_output(output_pack: TranslatorOutputPackage):
    message = output_pack.inner_output
    if isinstance(message, TgCommand):
        return message
    outer_context = output_pack.outer_context #type: TgContext
    content_arg = _get_content_arg(message)
    if content_arg is not None:
        return TgCommand.mock().send_message(chat_id=outer_context.chat_id, **content_arg)
    if isinstance(message, prim.Options):
        content_arg = _get_content_arg(message.content)
        buttons = _get_keyboard(message.options)
        return TgCommand.mock().send_message(chat_id = outer_context.chat_id, **content_arg, reply_markup=buttons)
    if isinstance(message, prim.Audio):
        with TempFile(Path(tempfile.gettempdir())/(str(uuid.uuid4())+'.wav')) as path:
            with open(path, 'wb') as stream:
                stream.write(message.data)
            return TgCommand.mock().send_voice(chat_id=outer_context.chat_id, voice=path)
    elif isinstance(message, prim.Image):
        with TempFile(Path(tempfile.gettempdir())/(str(uuid.uuid4())+'.png')) as path:
            with open(path, 'wb') as stream:
                stream.write(message.data)
            return TgCommand.mock().send_photo(chat_id=outer_context.chat_id, photo=open(path,'rb'))
    if isinstance(message, prim.Delete):
        return TgCommand.mock().delete_message(chat_id = outer_context.chat_id, message_id= message.id)
    return message


class TelegramTranslator(Translator):
    def __init__(self, inner_subroutine):
        super().__init__(
            inner_subroutine,
            context_translator=_translate_context,
            input_generator_translator=_translate_input,
            output_function_translator=_translate_output,
        )







