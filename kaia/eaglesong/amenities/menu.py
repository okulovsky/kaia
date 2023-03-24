from ..arch import *
from ..telegram import TgUpdate, TgCommand


import telegram as tg
from yo_fluq_ds import *

class MenuItemStatus(Enum):
    Active = 0
    Hidden = 1


class AbstractTelegramMenuItem(Subroutine):
    def get_caption(self):
        raise NotImplementedError()

    def run(self, c: Callable[[], TgUpdate]):
        raise NotImplementedError()

    def get_status(self) -> MenuItemStatus:
        return MenuItemStatus.Active


class MenuItemOverRoutine(AbstractTelegramMenuItem):
    def __init__(self, caption, method):
        self.caption = caption
        self.method = method

    def get_caption(self):
        return self.caption

    def run(self, c: Callable[[], TgUpdate]):
        yield FunctionalSubroutine.ensure(self.method)


class MenuItemInternal:
    def __init__(
            self,
            action: str,
            title: str,
            item: Optional[AbstractTelegramMenuItem]=None,
            special_action: Optional[str] = None
    ):
        self.action = action
        self.title = title
        self.item = item
        self.special_action = special_action


class TextMenuItem(AbstractTelegramMenuItem):
    def __init__(self,
                 name: str,
                 prompt: Union[str, Callable],
                 column_count: Optional[int] = 1,
                 add_back_button: bool = True,
                 add_reload_button: bool = True,
                 add_close_button: bool = True
                 ):
        self.name = name
        self.prompt = prompt
        self.colummn_count = column_count
        self.children = []
        self.add_back_button = add_back_button
        self.add_reload_button = add_reload_button
        self.add_close_button = add_close_button

    def add_child(self, item: AbstractTelegramMenuItem) -> 'TextMenuItem':
        self.children.append(item)
        return self


    def get_caption(self):
        return self.name


    def build_prompt_and_menu_items(self):
        if callable(self.prompt):
            prompt = self.prompt()
        else:
            prompt = self.prompt

        items = []

        for index, item in enumerate(self.children):
            name = item.get_caption()
            status = item.get_status()

            if status!=MenuItemStatus.Hidden:
                items.append(MenuItemInternal(
                    str(index),
                    name,
                    item,
                    None
                ))

        if self.add_back_button:
            items.append(MenuItemInternal(
                'back',
                'Back',
                special_action='back'
            ))

        if self.add_reload_button:
            items.append(MenuItemInternal(
                'reload',
                "Reload",
                special_action='reload'
            ))

        if self.add_close_button:
            items.append(MenuItemInternal(
                'close',
                'Close',
                special_action='close'
            ))
        return prompt, items

    def build_keyboard(self, items: List[MenuItemInternal]):
        buttons = []
        buffer = []
        for index, child in enumerate(items):
            item = tg.InlineKeyboardButton(child.title, callback_data=child.action, )
            buffer.append(item)
            if self.colummn_count is not None and len(buffer) > self.colummn_count:
                buttons.append(buffer)
                buffer = []
        if len(buffer) > 0:
            buttons.append(buffer)
        keyboard = tg.InlineKeyboardMarkup(buttons)
        return keyboard

    def run(self, c: Callable[[], TgUpdate]):
        while True:
            prompt, items = self.build_prompt_and_menu_items()
            keyboard = self.build_keyboard(items)
            yield TgCommand.mock().send_message(chat_id=c().chat_id, text=prompt, reply_markup=keyboard)
            message_id = c().last_return.message_id
            yield Listen()
            yield TgCommand.mock().delete_message(chat_id = c().chat_id, message_id=message_id)
            if c().type != TgUpdate.Type.Callback:
                yield Terminate(f'Expecting callback, but got {c().type}')
            action = Query.en(items).where(lambda z: z.action==c().update.callback_query.data).single_or_default() #type: MenuItemInternal
            if action is None:
                continue
            elif action.item is not None:
                yield FunctionalSubroutine(action.item.run)
            elif action.special_action == 'reload':
                continue
            elif action.special_action == 'back':
                yield Return()
            elif action.special_action == 'close':
                break

