import os
import uuid
from typing import *
from kaia.eaglesong.core import BotContext, primitives as prim, Translator, TranslatorInputPackage, TranslatorOutputPackage
from .primitives import TgContext, TgCommand, TgUpdatePackage, TgChannel, TgFunction
import telegram as tg
from kaia.infra import Loc


BUTTON_PREFIX = 'button_'

def _translate_context(context: TgContext):
    return BotContext(context.chat_id)

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
        uid = str(uuid.uuid4())
        path = Loc.temp_folder/'telegram_files'/uid
        os.makedirs(path.parent, exist_ok=True)
        with open(path, 'wb') as stream:
            stream.write(message.data)
        return TgCommand.mock().send_voice(chat_id=outer_context.chat_id, voice=path)
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







