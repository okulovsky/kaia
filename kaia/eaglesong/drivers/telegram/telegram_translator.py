from typing import *
from kaia.eaglesong.core import Routine, ContextTranslator, BotContext, TranslationContext, TranslationFilter, primitives as prim
from .primitives import TgContext, TgUpdatePackage, TgCommand
import telegram

import re
from datetime import datetime
import telegram as tg

BUTTON_PREFIX = 'button_'

def _get_inner_context_message(outer_context: TgContext):
    if outer_context.update_type == TgUpdatePackage.Type.Callback:
        button_id = outer_context.update.callback_query.data
        if not button_id.startswith(BUTTON_PREFIX):
            raise ValueError(f'Bad update: {outer_context.update}')
        return prim.SelectedOption(button_id[len(BUTTON_PREFIX):])
    elif outer_context.update_type == TgUpdatePackage.Type.Start or outer_context.update_type == TgUpdatePackage.Type.Text:
        return outer_context.update.message.text
    elif outer_context.update_type == TgUpdatePackage.Type.Timer:
        return prim.TimerTick()
    elif outer_context.update_type == TgUpdatePackage.Type.Feedback:
        if isinstance(outer_context.update, tg.Message):
            return outer_context.update.message_id
        else:
            return outer_context.update
    elif outer_context.update_type == TgUpdatePackage.Type.EaglesongFeedback:
        return outer_context.update
    raise ValueError(f'cannot translate context of type {outer_context.update_type}')


class TelegramContextTranslator(ContextTranslator):
    def create_inner_context(self, outer_context):
        return BotContext(outer_context.chat_id)

    def update_inner_context(self, outer_context: TgContext, inner_context: BotContext):
        inner_context.input = _get_inner_context_message(outer_context)
        inner_context.timestamp = datetime.now()



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


def _get_translated_message(context: TgContext, message):
    content_arg = _get_content_arg(message)
    if content_arg is not None:
        return TgCommand.mock().send_message(chat_id=context.chat_id, **content_arg)
    if isinstance(message, prim.Options):
        content_arg = _get_content_arg(message.content)
        buttons = _get_keyboard(message.options)
        return TgCommand.mock().send_message(chat_id = context.chat_id, **content_arg, reply_markup=buttons)
    if isinstance(message, prim.Delete):
        return TgCommand.mock().delete_message(chat_id = context.chat_id, message_id= message.id)
    if isinstance(message, prim.IsThinking):
        return TgCommand.mock().send_chat_action(chat_id = context.chat_id, action=telegram.constants.ChatAction.TYPING)
    return message


class TelegramMessageTranslator(Routine):
    def run(self, c: TranslationContext[Any, TgContext]):
        yield _get_translated_message(c.outer_context, c.inner_message)


class TelegramTranslationFilter(TranslationFilter):
    def __init__(self, inner_subroutine):
        super(TelegramTranslationFilter, self).__init__(
            inner_subroutine,
            TelegramContextTranslator(),
            TelegramMessageTranslator()
        )






